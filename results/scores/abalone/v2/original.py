"""Abalone, implemented solely from the supplied German rulebook."""
from dataclasses import dataclass
from typing import Optional

RADIUS = 4
DIRS = {"E": (1, 0), "NE": (1, -1), "NW": (0, -1),
        "W": (-1, 0), "SW": (-1, 1), "SE": (0, 1)}
COLORS = ("black", "white")
CELLS = tuple((q, r) for q in range(-4, 5) for r in range(-4, 5)
              if abs(q + r) <= 4)


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    group: tuple = ()
    direction: Optional[str] = None


@dataclass
class GameState:
    board: dict
    current_player: int
    captures: list
    terminal: bool = False
    winner: Optional[int] = None
    phase: str = "play"
    move_number: int = 0
    seed: Optional[int] = None


def _add(a, b):
    return a[0] + b[0], a[1] + b[1]


def _key(cell):
    return f"{cell[0]},{cell[1]}"


def _cell(text):
    q, r = text.split(",")
    return int(q), int(r)


class Game:
    def __init__(self, num_players=None, seed=None):
        if num_players is None:
            num_players = 2
        if num_players != 2:
            raise ValueError("the supplied game supports exactly 2 players")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise ValueError("seed must be an integer or None")
        self.num_players, self.seed = 2, seed

    def initial_state(self):
        board = {c: None for c in CELLS}
        black = ([(q, -4) for q in range(5)] +
                 [(q, -3) for q in range(-1, 4)] +
                 [(q, -2) for q in range(3)])
        white = ([(q, 4) for q in range(-4, 1)] +
                 [(q, 3) for q in range(-3, 2)] +
                 [(q, 2) for q in range(-2, 1)])
        for c in black: board[c] = "black"
        for c in white: board[c] = "white"
        return GameState(board, 0, [0, 0], seed=self.seed)

    def current_player(self, state):
        return state.current_player

    def _groups(self, state):
        color = COLORS[state.current_player]
        occupied = [c for c in CELLS if state.board[c] == color]
        groups = {(c,) for c in occupied}
        axes = ((1, 0), (1, -1), (0, -1))
        for start in occupied:
            for d in axes:
                line = [start]
                for _ in range(2):
                    line.append(_add(line[-1], d))
                    if line[-1] not in state.board or state.board[line[-1]] != color:
                        break
                    groups.add(tuple(line))
        return sorted(groups, key=lambda g: (len(g), tuple(_key(c) for c in g)))

    def _legal_move(self, state, group, direction):
        d = DIRS[direction]
        targets = [_add(c, d) for c in group]
        group_set = set(group)
        # Side-step: all destination hollows must be free.
        if all(t in state.board and (t in group_set or state.board[t] is None)
               for t in targets):
            return True
        # Inline: group and direction must share a line, with a leading marble.
        if len(group) == 1:
            return False
        if not any(_add(c, d) in group_set for c in group):
            return False
        front = next((c for c in group if _add(c, d) not in group_set), None)
        if front is None:
            return False
        pos, opponents = _add(front, d), 0
        enemy = COLORS[1 - state.current_player]
        while pos in state.board and state.board[pos] == enemy:
            opponents += 1
            pos = _add(pos, d)
        return 0 < opponents < len(group) and opponents <= 2 and (
            pos not in state.board or state.board[pos] is None)

    def legal_actions(self, state):
        if state.terminal:
            return []
        actions = [Action("move", state.current_player, g, direction)
                   for g in self._groups(state) for direction in DIRS
                   if self._legal_move(state, g, direction)]
        return actions or [Action("pass", state.current_player)]

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        board = dict(state.board)
        captures = list(state.captures)
        if action.type == "move":
            d, group = DIRS[action.direction], set(action.group)
            # Move the complete occupied chain ahead of the selected group.
            front = next(c for c in group if _add(c, d) not in group)
            chain = list(group)
            pos = _add(front, d)
            while pos in board and board[pos] is not None:
                chain.append(pos)
                pos = _add(pos, d)
            for c in sorted(chain, key=lambda x: x[0]*d[0] + x[1]*d[1], reverse=True):
                target = _add(c, d)
                piece = board[c]
                if target in board:
                    board[target] = piece
                elif piece != COLORS[state.current_player]:
                    captures[state.current_player] += 1
                board[c] = None
        terminal = captures[state.current_player] >= 6
        return GameState(board, state.current_player if terminal else 1-state.current_player,
                         captures, terminal, state.current_player if terminal else None,
                         "terminal" if terminal else "play", state.move_number + 1,
                         state.seed)

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0, 0]
        return [1 if i == state.winner else -1 for i in range(2)]

    def action_to_name(self, action):
        if action.type == "pass":
            return f"P{action.actor} pass"
        return f"P{action.actor} move {'+'.join(_key(c) for c in action.group)} {action.direction}"

    def name_to_action(self, name):
        parts = name.split()
        if len(parts) == 2 and parts[1] == "pass":
            return Action("pass", int(parts[0][1:]))
        if len(parts) == 4 and parts[1] == "move":
            return Action("move", int(parts[0][1:]),
                          tuple(_cell(x) for x in parts[2].split("+")), parts[3])
        raise ValueError("invalid action name")

    def render(self, state):
        rows = []
        for r in range(-4, 5):
            cells = [(q, r) for q in range(-4, 5) if (q, r) in state.board]
            rows.append(" " * abs(r) + " ".join(
                "." if state.board[c] is None else state.board[c][0].upper()
                for c in cells))
        return "\n".join(rows) + f"\nturn={state.current_player} captures={state.captures}"

    def action_to_data(self, action):
        args = {} if action.type == "pass" else {
            "group": [_key(c) for c in action.group], "direction": action.direction}
        return {"schema": "boardbench/abalone/action/1",
                "data": {"type": action.type, "actor": action.actor, "args": args}}

    def action_from_data(self, payload):
        self._envelope(payload, "boardbench/abalone/action/1")
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or type(d["actor"]) is not int or d["actor"] not in (0, 1) or type(d["args"]) is not dict:
            raise ValueError("invalid action payload")
        if d["type"] == "pass" and not d["args"]:
            return Action("pass", d["actor"])
        if d["type"] == "move" and set(d["args"]) == {"group", "direction"}:
            group, direction = d["args"]["group"], d["args"]["direction"]
            if type(group) is list and 1 <= len(group) <= 3 and direction in DIRS:
                cells = tuple(_cell(x) for x in group if type(x) is str)
                if len(cells) == len(group) and len(set(cells)) == len(cells) and all(c in CELLS for c in cells):
                    return Action("move", d["actor"], cells, direction)
        raise ValueError("invalid action payload")

    def state_to_data(self, state):
        data = {"configuration": {"players": 2, "seed": state.seed, "variant": "base"},
                "board": {_key(c): state.board[c] for c in CELLS},
                "current_player": state.current_player, "captures": list(state.captures),
                "terminal": state.terminal, "winner": state.winner, "phase": state.phase,
                "move_number": state.move_number, "pending": None,
                "chance": {"seed": state.seed}}
        return {"schema": "boardbench/abalone/state/1", "data": data}

    def state_from_data(self, payload):
        self._envelope(payload, "boardbench/abalone/state/1")
        d = payload["data"]
        required = {"configuration","board","current_player","captures","terminal",
                    "winner","phase","move_number","pending","chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        cfg = d["configuration"]
        if cfg != {"players": 2, "seed": cfg.get("seed") if type(cfg) is dict else None, "variant": "base"}:
            raise ValueError("invalid configuration")
        seed = cfg["seed"]
        valid_seed = seed is None or (type(seed) is int)
        valid = (valid_seed and type(d["board"]) is dict and set(d["board"]) == {_key(c) for c in CELLS}
                 and all(v in (None, *COLORS) for v in d["board"].values())
                 and type(d["current_player"]) is int and d["current_player"] in (0,1)
                 and type(d["captures"]) is list and len(d["captures"]) == 2
                 and all(type(x) is int and x >= 0 for x in d["captures"])
                 and type(d["terminal"]) is bool and d["winner"] in (None,0,1)
                 and d["phase"] in ("play","terminal") and type(d["move_number"]) is int
                 and d["move_number"] >= 0 and d["pending"] is None
                 and d["chance"] == {"seed": seed})
        if not valid:
            raise ValueError("invalid state payload")
        return GameState({_cell(k): v for k,v in d["board"].items()}, d["current_player"],
                         list(d["captures"]), d["terminal"], d["winner"], d["phase"],
                         d["move_number"], seed)

    def observation_to_data(self, state, player):
        if type(player) is not int or player not in (0,1):
            raise ValueError("invalid player")
        s = self.state_to_data(state)["data"]
        data = {"player": player, **{k: s[k] for k in
                ("board","current_player","captures","terminal","winner","phase","move_number")}}
        return {"schema": "boardbench/abalone/observation/1", "data": data}

    @staticmethod
    def _envelope(payload, schema):
        if type(payload) is not dict or set(payload) != {"schema","data"} or payload["schema"] != schema or type(payload["data"]) is not dict:
            raise ValueError("invalid canonical envelope")
