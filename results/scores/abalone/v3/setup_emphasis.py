"""Small, rulebook-faithful Abalone environment (two-player base game)."""

from dataclasses import dataclass


SCHEMA = "boardbench/abalone"
COLORS = ("black", "white")
DIRECTIONS = {
    "E": (1, 0), "NE": (1, -1), "NW": (0, -1),
    "W": (-1, 0), "SW": (-1, 1), "SE": (0, 1),
}


def _cells():
    return tuple(
        (q, r) for r in range(-4, 5) for q in range(-4, 5)
        if max(abs(q), abs(r), abs(q + r)) <= 4
    )


CELLS = _cells()
CELL_SET = frozenset(CELLS)


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    group: tuple = ()
    direction: str = ""


@dataclass(frozen=True)
class GameState:
    configuration: dict
    board: dict
    current_player: int
    captures: tuple
    terminal: bool
    winner: object
    phase: str
    move_number: int
    pending: object = None
    chance: dict = None


def _key(cell):
    return f"{cell[0]},{cell[1]}"


def _parse_cell(value):
    if not isinstance(value, str) or value.count(",") != 1:
        raise ValueError("cell must be '<q>,<r>'")
    a, b = value.split(",")
    try:
        cell = (int(a), int(b))
    except ValueError as exc:
        raise ValueError("cell coordinates must be integers") from exc
    if _key(cell) != value or cell not in CELL_SET:
        raise ValueError("invalid or non-canonical board cell")
    return cell


def _line(group):
    """Return the unsigned unit axis of a straight contiguous group."""
    if len(group) == 1:
        return None
    group = set(group)
    for d in DIRECTIONS.values():
        for start in group:
            if {(start[0] + i*d[0], start[1] + i*d[1])
                    for i in range(len(group))} == group:
                return d
    return None


class Game:
    def __init__(self, num_players=None, seed=None):
        if num_players is None:
            num_players = 2
        if type(num_players) is not int or num_players != 2:
            raise ValueError("the supplied rulebook supports exactly 2 players")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self):
        board = {c: None for c in CELLS}
        # Figure 1: two full back rows and the central three of the next row.
        for c in CELLS:
            q, r = c
            if r in (-4, -3) or (r == -2 and q in (0, 1, 2)):
                board[c] = "black"
            elif r in (3, 4) or (r == 2 and q in (-2, -1, 0)):
                board[c] = "white"
        return GameState(
            {"players": 2, "seed": self.seed, "variant": "base"}, board, 0,
            (0, 0), False, None, "play", 0, None, {"seed": self.seed}
        )

    def current_player(self, state):
        return state.current_player

    def _result(self, state, action):
        board = state.board
        group = action.group
        d = DIRECTIONS[action.direction]
        axis = _line(group)
        inline = len(group) > 1 and (d == axis or d == (-axis[0], -axis[1]))
        if not inline:
            destinations = [(c[0] + d[0], c[1] + d[1]) for c in group]
            if all(x in CELL_SET and board[x] is None for x in destinations):
                moved = dict(board)
                for c in group:
                    moved[c] = None
                for c in destinations:
                    moved[c] = COLORS[action.actor]
                return moved, None
            return None

        front = max(group, key=lambda c: c[0]*d[0] + c[1]*d[1])
        nxt = (front[0] + d[0], front[1] + d[1])
        if nxt in CELL_SET and board[nxt] is None:
            moved = dict(board)
            back = min(group, key=lambda c: c[0]*d[0] + c[1]*d[1])
            moved[back] = None
            moved[nxt] = COLORS[action.actor]
            return moved, None
        opponent = COLORS[1 - action.actor]
        chain = []
        while nxt in CELL_SET and board[nxt] == opponent:
            chain.append(nxt)
            nxt = (nxt[0] + d[0], nxt[1] + d[1])
        if not chain or len(chain) >= len(group):
            return None
        if nxt in CELL_SET and board[nxt] is not None:
            return None
        moved = dict(board)
        back = min(group, key=lambda c: c[0]*d[0] + c[1]*d[1])
        moved[back] = None
        for c in reversed(chain):
            dest = (c[0] + d[0], c[1] + d[1])
            if dest in CELL_SET:
                moved[dest] = opponent
        moved[(front[0] + d[0], front[1] + d[1])] = COLORS[action.actor]
        return moved, 1 - action.actor if nxt not in CELL_SET else None

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        own = sorted(c for c, value in state.board.items()
                     if value == COLORS[state.current_player])
        groups = {(c,) for c in own}
        for size in (2, 3):
            for start in own:
                for d in DIRECTIONS.values():
                    group = tuple(sorted(
                        (start[0] + i*d[0], start[1] + i*d[1])
                        for i in range(size)
                    ))
                    if all(c in own for c in group) and _line(group):
                        groups.add(group)
        actions = []
        for group in sorted(groups):
            for direction in DIRECTIONS:
                action = Action("move", state.current_player, group, direction)
                if self._result(state, action) is not None:
                    actions.append(action)
        return actions

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        board, captured = self._result(state, action)
        captures = list(state.captures)
        if captured is not None:
            captures[action.actor] += 1
        terminal = captures[action.actor] >= 6
        return GameState(
            dict(state.configuration), board,
            state.current_player if terminal else 1 - state.current_player,
            tuple(captures), terminal, action.actor if terminal else None,
            "terminal" if terminal else "play", state.move_number + 1,
            None, dict(state.chance)
        )

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0.0, 0.0]
        return [1.0 if i == state.winner else -1.0 for i in range(2)]

    def render(self, state):
        rows = []
        for r in range(-4, 5):
            cells = [c for c in CELLS if c[1] == r]
            rows.append(" " * abs(r) + " ".join(
                {"black": "B", "white": "W", None: "."}[state.board[c]]
                for c in cells
            ))
        return "\n".join(rows) + (
            f"\nturn={state.current_player} captures={state.captures}"
        )

    def action_to_name(self, action):
        if action.type == "pass":
            return f"pass | actor {action.actor}"
        cells = " ".join(_key(c) for c in action.group)
        return f"move | actor {action.actor} | group {cells} | {action.direction}"

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError("action name must be a string")
        parts = name.split(" | ")
        if len(parts) == 2 and parts[0] == "pass" and parts[1].startswith("actor "):
            try:
                return Action("pass", int(parts[1][6:]))
            except ValueError as exc:
                raise ValueError("invalid action name") from exc
        if (len(parts) != 4 or parts[0] != "move"
                or not parts[1].startswith("actor ")
                or not parts[2].startswith("group ")
                or parts[3] not in DIRECTIONS):
            raise ValueError("invalid action name")
        try:
            actor = int(parts[1][6:])
            group = tuple(_parse_cell(x) for x in parts[2][6:].split())
        except ValueError as exc:
            raise ValueError("invalid action name") from exc
        action = Action("move", actor, group, parts[3])
        if self.action_to_name(action) != name:
            raise ValueError("non-canonical action name")
        return action

    def state_to_data(self, state):
        data = {
            "configuration": dict(state.configuration),
            "board": {_key(c): state.board[c] for c in CELLS},
            "current_player": state.current_player,
            "captures": list(state.captures),
            "terminal": state.terminal, "winner": state.winner,
            "phase": state.phase, "move_number": state.move_number,
            "pending": None, "chance": dict(state.chance),
        }
        return {"schema": f"{SCHEMA}/state/1", "data": data}

    def state_from_data(self, payload):
        data = self._envelope(payload, "state")
        required = {"configuration", "board", "current_player", "captures",
                    "terminal", "winner", "phase", "move_number", "pending",
                    "chance"}
        if set(data) != required:
            raise ValueError("invalid state fields")
        cfg = data["configuration"]
        if (type(cfg) is not dict or set(cfg) != {"players", "seed", "variant"}
                or cfg["players"] != 2 or cfg["variant"] != "base"
                or (cfg["seed"] is not None and type(cfg["seed"]) is not int)):
            raise ValueError("invalid configuration")
        if type(data["board"]) is not dict or set(data["board"]) != {_key(c) for c in CELLS}:
            raise ValueError("invalid board")
        board = {}
        for key, value in data["board"].items():
            if value not in (None, *COLORS):
                raise ValueError("invalid marble color")
            board[_parse_cell(key)] = value
        cp, captures = data["current_player"], data["captures"]
        if type(cp) is not int or cp not in (0, 1):
            raise ValueError("invalid current player")
        if (type(captures) is not list or len(captures) != 2
                or any(type(x) is not int or x < 0 for x in captures)):
            raise ValueError("invalid captures")
        if type(data["terminal"]) is not bool or data["winner"] not in (None, 0, 1):
            raise ValueError("invalid terminal fields")
        if data["phase"] not in ("play", "terminal"):
            raise ValueError("invalid phase")
        if type(data["move_number"]) is not int or data["move_number"] < 0:
            raise ValueError("invalid move number")
        if data["pending"] is not None:
            raise ValueError("pending must be null")
        chance = data["chance"]
        if (type(chance) is not dict or set(chance) != {"seed"}
                or (chance["seed"] is not None and type(chance["seed"]) is not int)):
            raise ValueError("invalid chance")
        return GameState(dict(cfg), board, cp, tuple(captures), data["terminal"],
                         data["winner"], data["phase"], data["move_number"],
                         None, dict(chance))

    def action_to_data(self, action):
        if not isinstance(action, Action) or action.type not in ("move", "pass"):
            raise ValueError("invalid action")
        if type(action.actor) is not int or action.actor not in (0, 1):
            raise ValueError("invalid actor")
        if action.type == "pass":
            args = {}
        else:
            if (not 1 <= len(action.group) <= 3 or len(set(action.group)) != len(action.group)
                    or any(c not in CELL_SET for c in action.group)
                    or action.direction not in DIRECTIONS):
                raise ValueError("invalid move")
            args = {"group": [_key(c) for c in action.group],
                    "direction": action.direction}
        return {"schema": f"{SCHEMA}/action/1",
                "data": {"type": action.type, "actor": action.actor, "args": args}}

    def action_from_data(self, payload):
        data = self._envelope(payload, "action")
        if set(data) != {"type", "actor", "args"}:
            raise ValueError("invalid action fields")
        if type(data["actor"]) is not int or data["actor"] not in (0, 1):
            raise ValueError("invalid actor")
        if data["type"] == "pass" and type(data["args"]) is dict and not data["args"]:
            return Action("pass", data["actor"])
        if data["type"] != "move" or type(data["args"]) is not dict or set(data["args"]) != {"group", "direction"}:
            raise ValueError("invalid action type or arguments")
        group = data["args"]["group"]
        if type(group) is not list or not 1 <= len(group) <= 3:
            raise ValueError("invalid group")
        action = Action("move", data["actor"],
                        tuple(_parse_cell(x) for x in group),
                        data["args"]["direction"])
        self.action_to_data(action)
        return action

    def observation_to_data(self, state, player):
        if type(player) is not int or player not in (0, 1):
            raise ValueError("invalid player")
        source = self.state_to_data(state)["data"]
        data = {k: source[k] for k in (
            "board", "current_player", "captures", "terminal", "winner",
            "phase", "move_number"
        )}
        data = {"player": player, **data}
        return {"schema": f"{SCHEMA}/observation/1", "data": data}

    @staticmethod
    def _envelope(payload, suffix):
        if (type(payload) is not dict or set(payload) != {"schema", "data"}
                or payload["schema"] != f"{SCHEMA}/{suffix}/1"
                or type(payload["data"]) is not dict):
            raise ValueError(f"invalid {suffix} envelope")
        return payload["data"]
