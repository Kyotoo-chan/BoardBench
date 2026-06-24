from dataclasses import dataclass
import math

TERMINAL = -1

EMPTY = -1
RED = 0
BLACK = 1

PLAYER_NAMES = ("Red", "Black")
SYMBOLS = {EMPTY: ".", RED: "R", BLACK: "B"}

SIDE_LENGTH = 8
RADIUS = SIDE_LENGTH - 1
STONES_PER_PLAYER = 55

# Axial-neighbor directions on the triangular/hexagonal point grid.
DIRECTIONS = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


def _sign_label(value):
    if value > 0:
        return "p" + str(value)
    if value < 0:
        return "n" + str(-value)
    return "z0"


def _parse_signed_label(text):
    if len(text) < 2:
        raise ValueError("bad signed coordinate")
    sign = text[0]
    digits = text[1:]
    if sign not in ("p", "n", "z") or not digits.isdigit():
        raise ValueError("bad signed coordinate")
    if sign == "z":
        if digits != "0":
            raise ValueError("zero must be encoded as z0")
        return 0
    if len(digits) > 1 and digits[0] == "0":
        raise ValueError("non-canonical leading zero")
    value = int(digits)
    if value <= 0:
        raise ValueError("p/n coordinates must be nonzero")
    return value if sign == "p" else -value


def _q_range_for_r(r):
    return max(-RADIUS, -r - RADIUS), min(RADIUS, -r + RADIUS)


def _build_points():
    points = []
    for r in range(-RADIUS, RADIUS + 1):
        q_min, q_max = _q_range_for_r(r)
        for q in range(q_min, q_max + 1):
            points.append((q, r))
    return tuple(points)


def _cube(point):
    q, r = point
    return q, r, -q - r


def _xy(point):
    q, r = point
    # Affine integer embedding of the axial grid.
    return 2 * q + r, 2 * r


POINTS = _build_points()
POINT_SET = frozenset(POINTS)
POINT_TO_INDEX = {p: i for i, p in enumerate(POINTS)}

NEIGHBORS = {
    p: tuple(
        (p[0] + dq, p[1] + dr)
        for dq, dr in DIRECTIONS
        if (p[0] + dq, p[1] + dr) in POINT_SET
    )
    for p in POINTS
}

CORNERS = frozenset(
    p for p in POINTS if sum(1 for v in _cube(p) if abs(v) == RADIUS) == 2
)
BOUNDARY_POINTS = frozenset(
    p for p in POINTS if any(abs(v) == RADIUS for v in _cube(p))
)


def _build_sides():
    sides = []
    for axis, value in (
        ("q", RADIUS),
        ("q", -RADIUS),
        ("r", RADIUS),
        ("r", -RADIUS),
        ("s", RADIUS),
        ("s", -RADIUS),
    ):
        label = axis + "=" + _sign_label(value)
        pts = []
        for p in POINTS:
            q, r, s = _cube(p)
            coord = {"q": q, "r": r, "s": s}[axis]
            if coord == value and p not in CORNERS:
                pts.append(p)
        sides.append((label, frozenset(pts)))
    return tuple(sides)


SIDES = _build_sides()
POINT_TO_SIDE_LABELS = {
    p: tuple(label for label, side_points in SIDES if p in side_points)
    for p in POINTS
}


def _coord_to_label(point):
    q, r = point
    return "q{}_r{}".format(_sign_label(q), _sign_label(r))


def _coord_from_label(label):
    if not label.startswith("q"):
        raise ValueError("coordinate must start with q")
    parts = label[1:].split("_r")
    if len(parts) != 2:
        raise ValueError("coordinate must be q..._r...")
    q = _parse_signed_label(parts[0])
    r = _parse_signed_label(parts[1])
    point = (q, r)
    if point not in POINT_SET:
        raise ValueError("coordinate is not on the board")
    return point


@dataclass(frozen=True)
class GameState:
    board: tuple
    current: int
    remaining: tuple
    terminal: bool = False
    winner: object = None
    win_condition: str = ""
    move_number: int = 0
    last_action: str = ""


class Game:
    """Havannah implementation from the supplied rule pages."""

    num_players = 2

    def __init__(self):
        self.points = POINTS
        self.sides = SIDES
        self.corners = CORNERS

    def initial_state(self):
        return GameState(
            board=(EMPTY,) * len(POINTS),
            current=RED,
            remaining=(STONES_PER_PLAYER, STONES_PER_PLAYER),
        )

    def current_player(self, state):
        return TERMINAL if self.is_terminal(state) else state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        player = state.current
        if player not in (RED, BLACK) or state.remaining[player] <= 0:
            return []
        return [
            ("place", q, r)
            for i, (q, r) in enumerate(POINTS)
            if state.board[i] == EMPTY
        ]

    def apply_action(self, state, action):
        if self.is_terminal(state):
            raise ValueError("cannot act in a terminal state")

        action = self._normalize_action(action)
        _, q, r = action
        point = (q, r)
        idx = POINT_TO_INDEX[point]
        player = state.current

        if player not in (RED, BLACK):
            raise ValueError("bad current player")
        if state.remaining[player] <= 0:
            raise ValueError("current player has no stones remaining")
        if state.board[idx] != EMPTY:
            raise ValueError("point is occupied")

        board = list(state.board)
        board[idx] = player
        board = tuple(board)

        remaining = list(state.remaining)
        remaining[player] -= 1
        remaining = tuple(remaining)

        condition = self._winning_condition(board, player)
        next_player = BLACK if player == RED else RED

        if condition:
            return GameState(
                board=board,
                current=next_player,
                remaining=remaining,
                terminal=True,
                winner=player,
                win_condition=condition,
                move_number=state.move_number + 1,
                last_action=self.action_to_name(action),
            )

        terminal_draw = remaining[next_player] <= 0 or EMPTY not in board
        return GameState(
            board=board,
            current=next_player,
            remaining=remaining,
            terminal=terminal_draw,
            winner=None,
            win_condition="",
            move_number=state.move_number + 1,
            last_action=self.action_to_name(action),
        )

    def is_terminal(self, state):
        if state.terminal or state.winner is not None:
            return True
        if state.current not in (RED, BLACK):
            return True
        if state.remaining[state.current] <= 0:
            return True
        if EMPTY not in state.board:
            return True
        return False

    def returns(self, state):
        if not self.is_terminal(state):
            return [0.0, 0.0]
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLACK:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def render(self, state):
        if self.is_terminal(state):
            turn = "terminal"
            result = "draw" if state.winner is None else (
                PLAYER_NAMES[state.winner] + ":" + state.win_condition
            )
        else:
            turn = PLAYER_NAMES[state.current]
            result = "ongoing"

        lines = [
            "turn={}; move={}; remaining=Red:{},Black:{}; result={}; last={}".format(
                turn,
                state.move_number,
                state.remaining[RED],
                state.remaining[BLACK],
                result,
                state.last_action or "-",
            ),
            "coords=axial(q,r); q increases left-to-right; .=empty R=red B=black",
        ]

        for r in range(-RADIUS, RADIUS + 1):
            q_min, q_max = _q_range_for_r(r)
            row = []
            for q in range(q_min, q_max + 1):
                row.append(SYMBOLS[state.board[POINT_TO_INDEX[(q, r)]]])
            indent = " " * abs(r)
            lines.append(
                "{}r={} q={}..{} | {}".format(
                    indent,
                    _sign_label(r),
                    _sign_label(q_min),
                    _sign_label(q_max),
                    " ".join(row),
                )
            )
        return "\n".join(lines)

    def action_to_name(self, action):
        action = self._normalize_action(action)
        _, q, r = action
        return "place:" + _coord_to_label((q, r))

    def name_to_action(self, name):
        if not isinstance(name, str) or not name.startswith("place:"):
            raise ValueError("bad action name")
        q, r = _coord_from_label(name[len("place:"):])
        return ("place", q, r)

    def _normalize_action(self, action):
        if isinstance(action, str):
            return self.name_to_action(action)
        if not isinstance(action, tuple) or len(action) != 3:
            raise ValueError("action must be ('place', q, r)")
        kind, q, r = action
        if kind != "place" or not isinstance(q, int) or not isinstance(r, int):
            raise ValueError("action must be ('place', q, r)")
        if (q, r) not in POINT_SET:
            raise ValueError("point is not on the board")
        return ("place", q, r)

    def _winning_condition(self, board, player):
        conditions = []
        if self._has_ring(board, player):
            conditions.append("ring")
        bridge, fork = self._has_bridge_and_fork(board, player)
        if bridge:
            conditions.append("bridge")
        if fork:
            conditions.append("fork")
        return "+".join(conditions)

    def _player_stones(self, board, player):
        return {POINTS[i] for i, value in enumerate(board) if value == player}

    def _has_bridge_and_fork(self, board, player):
        stones = self._player_stones(board, player)
        seen = set()
        has_bridge = False
        has_fork = False

        for start in stones:
            if start in seen:
                continue
            stack = [start]
            seen.add(start)
            component = []

            while stack:
                p = stack.pop()
                component.append(p)
                for nb in NEIGHBORS[p]:
                    if nb in stones and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)

            corner_count = sum(1 for p in component if p in CORNERS)
            side_labels = set()
            for p in component:
                side_labels.update(POINT_TO_SIDE_LABELS[p])

            if corner_count >= 2:
                has_bridge = True
            if len(side_labels) >= 3:
                has_fork = True
            if has_bridge and has_fork:
                return True, True

        return has_bridge, has_fork

    def _has_ring(self, board, player):
        # A ring is interpreted as a same-color cycle whose polygon contains
        # at least one board point, occupied or empty.
        stones = self._player_stones(board, player)
        if len(stones) < 6:
            return False

        unseen = set(stones)
        while unseen:
            start = unseen.pop()
            component = {start}
            stack = [start]
            edge_twice_count = 0

            while stack:
                p = stack.pop()
                for nb in NEIGHBORS[p]:
                    if nb in stones:
                        edge_twice_count += 1
                        if nb in unseen:
                            unseen.remove(nb)
                            component.add(nb)
                            stack.append(nb)

            edge_count = edge_twice_count // 2
            if edge_count >= len(component):
                if self._component_has_enclosing_cycle(component):
                    return True

        return False

    def _component_has_enclosing_cycle(self, component):
        adj = {}
        for p in component:
            px, py = _xy(p)
            ns = [nb for nb in NEIGHBORS[p] if nb in component]
            if ns:
                ns.sort(key=lambda n: math.atan2(_xy(n)[1] - py, _xy(n)[0] - px))
                adj[p] = ns

        directed_edges = [(p, nb) for p, ns in adj.items() for nb in ns]
        visited = set()

        for start_edge in directed_edges:
            if start_edge in visited:
                continue

            walk = []
            edge = start_edge
            while edge not in visited:
                visited.add(edge)
                u, v = edge
                walk.append(u)
                ns = adj[v]
                idx = ns.index(u)
                # Follow one face of the embedded graph.
                w = ns[(idx - 1) % len(ns)]
                edge = (v, w)

            for cycle in self._simple_cycles_from_closed_walk(walk):
                if self._cycle_encloses_board_point(cycle):
                    return True

        return False

    def _simple_cycles_from_closed_walk(self, walk):
        if not walk:
            return []
        sequence = list(walk) + [walk[0]]
        stack = []
        positions = {}
        cycles = []

        for v in sequence:
            if v in positions:
                i = positions[v]
                cycle = stack[i:]
                if len(cycle) >= 3:
                    cycles.append(tuple(cycle))
                for old in stack[i:]:
                    positions.pop(old, None)
                stack = stack[:i]
            positions[v] = len(stack)
            stack.append(v)

        return cycles

    def _cycle_encloses_board_point(self, cycle):
        cycle_set = set(cycle)
        poly = [_xy(p) for p in cycle]
        min_x = min(x for x, _ in poly)
        max_x = max(x for x, _ in poly)
        min_y = min(y for _, y in poly)
        max_y = max(y for _, y in poly)

        for p in POINTS:
            if p in cycle_set:
                continue
            x, y = _xy(p)
            if x < min_x or x > max_x or y < min_y or y > max_y:
                continue
            if self._point_strictly_inside_polygon((x, y), poly):
                return True
        return False

    def _point_strictly_inside_polygon(self, point, poly):
        x, y = point
        inside = False
        n = len(poly)

        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n)]

            cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
            if cross == 0 and min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
                return False

            if (y1 > y) != (y2 > y):
                x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x_intersect > x:
                    inside = not inside

        return inside
