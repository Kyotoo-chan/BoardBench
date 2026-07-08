Open questions / assumptions

- The figures are not available, so the exact board size, cone projection, and red/blue edge division are underspecified.
- This implements a configurable flat hexagonal explanation board, default `radius=3`.
- The outer edge is split into two equal arcs with two shared edge cells, matching the text's statement that shared edge cells belong to both players.
- "Surrounds the center" is interpreted graph-theoretically: the center cannot reach any outer boundary cell without crossing the relevant stones/edge segment.
- A full board with no winner is treated as a draw.

```python
from collections import deque
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Set, Tuple

TERMINAL = -1

RED = 0
BLUE = 1
PLAYER_NAMES = ("Red", "Blue")

Coord = Tuple[int, int]
Stone = Tuple[int, int, int]

DIRECTIONS: Tuple[Coord, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass(frozen=True)
class GameState:
    stones: Tuple[Stone, ...] = ()
    to_move: int = RED
    winner: Optional[int] = None
    history: Tuple[str, ...] = ()


class Game:
    """Conect implementation from the supplied text only.

    Missing figures leave the exact conic board geometry underspecified. This
    class uses a flat hexagonal explanation board with a split outer edge.
    """

    def __init__(self, radius: int = 3):
        if not isinstance(radius, int) or radius < 1:
            raise ValueError("radius must be a positive integer")

        self.radius = radius
        self.num_players = 2
        self.center: Coord = (0, 0)

        self.cells = tuple(sorted(self._make_cells(radius), key=self._coord_sort_key))
        self.cell_set = frozenset(self.cells)
        self.boundary = frozenset(c for c in self.cells if self._is_boundary(c))
        self.neighbors = {
            c: tuple(n for n in self._neighbor_coords(c) if n in self.cell_set)
            for c in self.cells
        }

        # Assumption: split the outer boundary into two equal colored arcs. The
        # endpoints of those arcs are the two shared edge cells.
        boundary_order = self._boundary_order()
        half = len(boundary_order) // 2
        self.shared_edge_cells = frozenset((boundary_order[0], boundary_order[half]))
        self.player_edge_lists = {
            RED: boundary_order[: half + 1],
            BLUE: boundary_order[half:] + boundary_order[:1],
        }
        self.player_edges = {
            RED: frozenset(self.player_edge_lists[RED]),
            BLUE: frozenset(self.player_edge_lists[BLUE]),
        }

    def initial_state(self) -> GameState:
        return GameState()

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        return state.to_move

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        board = self._board_dict(state)
        return [
            self._action_for_coord(coord)
            for coord in self.cells
            if coord not in board
        ]

    def apply_action(self, state: GameState, action: str) -> GameState:
        if self.is_terminal(state):
            raise ValueError("cannot apply an action to a terminal state")

        coord = self._parse_place_action(action)
        canonical = self._action_for_coord(coord)
        if action != canonical:
            raise ValueError("action is not in canonical form: %r" % (action,))

        board = self._board_dict(state)
        if coord in board:
            raise ValueError("cell is already occupied: %s" % self._coord_label(coord))

        player = state.to_move
        board[coord] = player
        winner = player if self._has_won(board, player) else None
        next_player = BLUE if player == RED else RED

        return GameState(
            stones=self._stones_tuple(board),
            to_move=next_player,
            winner=winner,
            history=state.history + (action,),
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or len(self._board_dict(state)) == len(self.cells)

    def returns(self, state: GameState) -> List[float]:
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLUE:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def render(self, state: GameState) -> str:
        board = self._board_dict(state)

        if state.winner is not None:
            status = "terminal:winner=%s" % PLAYER_NAMES[state.winner]
        elif len(board) == len(self.cells):
            status = "terminal:draw"
        else:
            status = "turn:%s" % PLAYER_NAMES[state.to_move]

        red_edge = "[" + ", ".join(self._coord_label(c) for c in self.player_edge_lists[RED]) + "]"
        blue_edge = "[" + ", ".join(self._coord_label(c) for c in self.player_edge_lists[BLUE]) + "]"

        lines = [
            status,
            "radius:%d" % self.radius,
            "moves:%d" % len(state.history),
            "last:%s" % (state.history[-1] if state.history else "-"),
            "legend:R=red_stone B=blue_stone r=red_edge b=blue_edge *=shared_edge .=empty",
            "red_edge:%s" % red_edge,
            "blue_edge:%s" % blue_edge,
            "board:",
        ]

        for r in range(-self.radius, self.radius + 1):
            q_min = max(-self.radius, -r - self.radius)
            q_max = min(self.radius, -r + self.radius)
            row = []
            for q in range(q_min, q_max + 1):
                coord = (q, r)
                row.append(self._cell_token(coord, board.get(coord)))
            lines.append(
                "r_%s q_%s..q_%s: %s"
                % (
                    self._signed_label(r),
                    self._signed_label(q_min),
                    self._signed_label(q_max),
                    " ".join(row),
                )
            )

        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        coord = self._parse_place_action(action)
        return self._action_for_coord(coord)

    def name_to_action(self, name: str) -> str:
        canonical = self.action_to_name(name)
        if canonical != name:
            raise ValueError("not a canonical action name: %r" % (name,))
        return canonical

    def _has_won(self, board: Dict[Coord, int], player: int) -> bool:
        own = {coord for coord, owner in board.items() if owner == player}
        edge = self.player_edges[player]

        if self._center_to_edge_path(own, edge):
            return True

        for component in self._components(own):
            if not (component & edge):
                continue

            if self._walls_enclose_center(component):
                return True

            if self._component_makes_edge_loop(component, player):
                return True

        return False

    def _center_to_edge_path(self, own: Set[Coord], edge: Set[Coord]) -> bool:
        if self.center not in own:
            return False
        center_component = self._component_from(self.center, own)
        return bool(center_component & edge)

    def _component_makes_edge_loop(self, component: Set[Coord], player: int) -> bool:
        edge_list = self.player_edge_lists[player]
        touched_indices = [i for i, coord in enumerate(edge_list) if coord in component]

        if len(touched_indices) < 2:
            return False

        for start, end in combinations(touched_indices, 2):
            # The rule text says the open path and intermediary edge cells form
            # the loop. The exact figure is unavailable, so the edge segment
            # between the two touched edge cells is used as that intermediary.
            edge_segment = set(edge_list[start : end + 1])
            if self._walls_enclose_center(set(component) | edge_segment):
                return True

        return False

    def _walls_enclose_center(self, walls: Iterable[Coord]) -> bool:
        blocked = set(walls)
        if self.center in blocked:
            return False

        seen = {self.center}
        queue = deque([self.center])

        while queue:
            coord = queue.popleft()
            if coord in self.boundary:
                return False

            for neighbor in self.neighbors[coord]:
                if neighbor not in blocked and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        return True

    def _components(self, cells: Set[Coord]) -> List[Set[Coord]]:
        remaining = set(cells)
        result = []

        while remaining:
            start = next(iter(remaining))
            component = self._component_from(start, remaining)
            result.append(component)
            remaining -= component

        return result

    def _component_from(self, start: Coord, allowed: Iterable[Coord]) -> Set[Coord]:
        allowed_set = set(allowed)
        if start not in allowed_set:
            return set()

        seen = {start}
        queue = deque([start])

        while queue:
            coord = queue.popleft()
            for neighbor in self.neighbors[coord]:
                if neighbor in allowed_set and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        return seen

    def _make_cells(self, radius: int) -> List[Coord]:
        cells = []
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                if max(abs(q), abs(r), abs(q + r)) <= radius:
                    cells.append((q, r))
        return cells

    def _boundary_order(self) -> Tuple[Coord, ...]:
        q, r = -self.radius, self.radius
        start = (q, r)
        order = []

        for dq, dr in DIRECTIONS:
            for _ in range(self.radius):
                order.append((q, r))
                q += dq
                r += dr

        if (q, r) != start:
            raise RuntimeError("internal boundary construction error")

        return tuple(order)

    def _neighbor_coords(self, coord: Coord) -> List[Coord]:
        q, r = coord
        return [(q + dq, r + dr) for dq, dr in DIRECTIONS]

    def _is_boundary(self, coord: Coord) -> bool:
        q, r = coord
        return max(abs(q), abs(r), abs(q + r)) == self.radius

    def _board_dict(self, state: GameState) -> Dict[Coord, int]:
        return {(q, r): player for q, r, player in state.stones}

    def _stones_tuple(self, board: Dict[Coord, int]) -> Tuple[Stone, ...]:
        return tuple(
            (q, r, board[(q, r)])
            for q, r in sorted(board.keys(), key=self._coord_sort_key)
        )

    def _action_for_coord(self, coord: Coord) -> str:
        return "place:%s" % self._coord_label(coord)

    def _parse_place_action(self, action: str) -> Coord:
        if not isinstance(action, str):
            raise TypeError("actions are canonical strings")
        if not action.startswith("place:"):
            raise ValueError("unknown action format: %r" % (action,))

        coord = self._parse_coord_label(action[len("place:") :])
        if coord not in self.cell_set:
            raise ValueError("coordinate is not on this board: %r" % (coord,))
        return coord

    def _coord_label(self, coord: Coord) -> str:
        if coord == self.center:
            return "center"
        q, r = coord
        return "q_%s,r_%s" % (self._signed_label(q), self._signed_label(r))

    def _parse_coord_label(self, label: str) -> Coord:
        if label == "center":
            return self.center

        parts = label.split(",")
        if len(parts) != 2 or not parts[0].startswith("q_") or not parts[1].startswith("r_"):
            raise ValueError("bad coordinate label: %r" % (label,))

        q = self._parse_signed(parts[0][2:])
        r = self._parse_signed(parts[1][2:])
        return (q, r)

    def _signed_label(self, value: int) -> str:
        if value == 0:
            return "z0"
        if value > 0:
            return "p%d" % value
        return "n%d" % (-value)

    def _parse_signed(self, text: str) -> int:
        if text == "z0":
            return 0
        if len(text) < 2:
            raise ValueError("bad signed number: %r" % (text,))

        sign = text[0]
        digits = text[1:]
        if not digits.isdigit():
            raise ValueError("bad signed number: %r" % (text,))

        value = int(digits)
        if value <= 0:
            raise ValueError("signed nonzero coordinates must not use zero: %r" % (text,))

        if sign == "p":
            return value
        if sign == "n":
            return -value

        raise ValueError("bad signed number: %r" % (text,))

    def _cell_token(self, coord: Coord, owner: Optional[int]) -> str:
        if owner == RED:
            return "R"
        if owner == BLUE:
            return "B"
        if coord in self.shared_edge_cells:
            return "*"
        if coord in self.player_edges[RED]:
            return "r"
        if coord in self.player_edges[BLUE]:
            return "b"
        return "."

    def _coord_sort_key(self, coord: Coord) -> Tuple[int, int]:
        q, r = coord
        return (r, q)
```