Could not write `outputs/havannah_agentic.py` because this session’s filesystem is read-only, and Python execution was also blocked by policy. Below is the exact final file content.

**Open Questions / Assumptions**
- Player `0` is red and moves first; player `1` is black.
- The 169-point board is modeled as a side-8 hexagonal point graph, inferred from the rulebook’s 169 points and board diagram.
- If all 55 stones per player are used without a win, the game is treated as a draw with returns `[0.0, 0.0]`.
- A ring is detected as a connected same-color component enclosing at least one board point; enclosed points may be empty or occupied by either color, as stated in the rulebook.

```python
"""Self-contained Havannah implementation from the supplied rulebook pages.

The rulebook describes a 169-point hexagonal board, 55 red stones, 55 black
stones, red to move first, alternating placement on empty points, no movement,
and no capture. The first player to make a ring, bridge, or fork wins.
"""

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Set, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

RED = 0
BLACK = 1
EMPTY: Optional[int] = None
PLAYER_NAMES = ("red", "black")
PLAYER_SYMBOLS = {EMPTY: ".", RED: "R", BLACK: "B"}

BOARD_SIDE = 8
BOARD_RADIUS = BOARD_SIDE - 1
STONES_PER_PLAYER = 55

Coord = Tuple[int, int]
Board = Tuple[Optional[int], ...]


def _on_board(q: int, r: int) -> bool:
    s = -q - r
    return max(abs(q), abs(r), abs(s)) <= BOARD_RADIUS


BOARD_COORDS: Tuple[Coord, ...] = tuple(
    (q, r)
    for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1)
    for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1)
    if _on_board(q, r)
)
POINT_COUNT = len(BOARD_COORDS)
INDEX_BY_COORD: Dict[Coord, int] = {coord: index for index, coord in enumerate(BOARD_COORDS)}

DIRECTIONS: Tuple[Coord, ...] = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
CORNER_COORDS: Tuple[Coord, ...] = (
    (0, -BOARD_RADIUS),
    (BOARD_RADIUS, -BOARD_RADIUS),
    (BOARD_RADIUS, 0),
    (0, BOARD_RADIUS),
    (-BOARD_RADIUS, BOARD_RADIUS),
    (-BOARD_RADIUS, 0),
)
CORNER_COORD_SET = frozenset(CORNER_COORDS)
CORNER_INDICES = frozenset(INDEX_BY_COORD[coord] for coord in CORNER_COORDS)


def _neighbor_indices(coord: Coord) -> Tuple[int, ...]:
    q, r = coord
    result: List[int] = []
    for dq, dr in DIRECTIONS:
        neighbor = (q + dq, r + dr)
        if neighbor in INDEX_BY_COORD:
            result.append(INDEX_BY_COORD[neighbor])
    return tuple(result)


NEIGHBORS: Tuple[Tuple[int, ...], ...] = tuple(_neighbor_indices(coord) for coord in BOARD_COORDS)


def _side_for_coord(coord: Coord) -> Optional[int]:
    if coord in CORNER_COORD_SET:
        return None
    q, r = coord
    s = -q - r
    if r == -BOARD_RADIUS:
        return 0
    if q == BOARD_RADIUS:
        return 1
    if s == -BOARD_RADIUS:
        return 2
    if r == BOARD_RADIUS:
        return 3
    if q == -BOARD_RADIUS:
        return 4
    if s == BOARD_RADIUS:
        return 5
    return None


SIDE_BY_INDEX: Tuple[Optional[int], ...] = tuple(_side_for_coord(coord) for coord in BOARD_COORDS)
BOUNDARY_INDICES: Tuple[int, ...] = tuple(
    index for index in range(POINT_COUNT) if index in CORNER_INDICES or SIDE_BY_INDEX[index] is not None
)
BOUNDARY_INDEX_SET = frozenset(BOUNDARY_INDICES)
IS_BOUNDARY: Tuple[bool, ...] = tuple(index in BOUNDARY_INDEX_SET for index in range(POINT_COUNT))
ROW_VALUES: Tuple[int, ...] = tuple(range(-BOARD_RADIUS, BOARD_RADIUS + 1))
ROWS: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(INDEX_BY_COORD[(q, r)] for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1) if (q, r) in INDEX_BY_COORD)
    for r in ROW_VALUES
)


def _signed(value: int) -> str:
    return ("p" if value >= 0 else "n") + str(abs(value))


def _parse_signed(token: str) -> int:
    if len(token) < 2 or token[0] not in ("p", "n") or not token[1:].isdigit():
        raise ValueError(f"Bad signed coordinate token: {token!r}")
    digits = token[1:]
    if len(digits) > 1 and digits.startswith("0"):
        raise ValueError(f"Non-canonical coordinate token: {token!r}")
    if token[0] == "n" and digits == "0":
        raise ValueError("Use p0, not n0, for zero coordinates.")
    value = int(digits)
    return value if token[0] == "p" else -value


def _coord_name(coord: Coord) -> str:
    q, r = coord
    return f"q_{_signed(q)}_r_{_signed(r)}"


def _parse_coord_name(text: str) -> Coord:
    parts = text.split("_")
    if len(parts) != 4 or parts[0] != "q" or parts[2] != "r":
        raise ValueError(f"Bad coordinate name: {text!r}")
    return (_parse_signed(parts[1]), _parse_signed(parts[3]))


def _axis_label(axis: str, value: int) -> str:
    return f"{axis}_{_signed(value)}"


@dataclass(frozen=True)
class GameState:
    board: Board
    player: int
    stones_remaining: Tuple[int, int]
    move_number: int = 0
    winner: Optional[int] = None
    win_type: Optional[str] = None
    history: Tuple[int, ...] = ()


class Game:
    num_players = 2
    player_names = PLAYER_NAMES
    board_side = BOARD_SIDE
    num_points = POINT_COUNT
    stones_per_player = STONES_PER_PLAYER

    def initial_state(self) -> GameState:
        return GameState(
            board=(EMPTY,) * POINT_COUNT,
            player=RED,
            stones_remaining=(STONES_PER_PLAYER, STONES_PER_PLAYER),
        )

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.player

    def legal_actions(self, state: GameState) -> List[int]:
        if len(state.board) != POINT_COUNT:
            return []
        if self.is_terminal(state) or state.player not in (RED, BLACK):
            return []
        if state.stones_remaining[state.player] <= 0:
            return []
        return [index for index, cell in enumerate(state.board) if cell is EMPTY]

    def apply_action(self, state: GameState, action: int) -> GameState:
        if self.is_terminal(state):
            raise ValueError("Cannot apply an action to a terminal state.")
        if len(state.board) != POINT_COUNT:
            raise ValueError("State board has the wrong number of points.")
        if state.player not in (RED, BLACK):
            raise ValueError(f"Bad player to move: {state.player!r}")
        if state.stones_remaining[state.player] <= 0:
            raise ValueError("The current player has no stones remaining.")
        if type(action) is not int:
            raise ValueError(f"Action must be an integer point id, got {action!r}.")
        if action < 0 or action >= POINT_COUNT:
            raise ValueError(f"Action out of range: {action!r}")
        if state.board[action] is not EMPTY:
            raise ValueError(f"Point is already occupied: {self.action_to_name(action)}")

        player = state.player
        board_list = list(state.board)
        board_list[action] = player
        new_board: Board = tuple(board_list)

        remaining = list(state.stones_remaining)
        remaining[player] -= 1
        new_remaining = (remaining[RED], remaining[BLACK])

        forms = _winning_forms(new_board, player)
        if forms:
            return GameState(
                board=new_board,
                player=TERMINAL,
                stones_remaining=new_remaining,
                move_number=state.move_number + 1,
                winner=player,
                win_type="+".join(forms),
                history=state.history + (action,),
            )

        next_player = BLACK if player == RED else RED
        next_to_move = next_player
        if new_remaining[next_player] <= 0 or not any(cell is EMPTY for cell in new_board):
            next_to_move = TERMINAL

        return GameState(
            board=new_board,
            player=next_to_move,
            stones_remaining=new_remaining,
            move_number=state.move_number + 1,
            winner=None,
            win_type=None,
            history=state.history + (action,),
        )

    def is_terminal(self, state: GameState) -> bool:
        if state.player == TERMINAL or state.winner is not None:
            return True
        if state.player in (RED, BLACK):
            if state.stones_remaining[state.player] <= 0:
                return True
            if not any(cell is EMPTY for cell in state.board):
                return True
        return False

    def returns(self, state: GameState) -> List[float]:
        if state.winner is None:
            return [0.0, 0.0]
        result = [-1.0, -1.0]
        result[state.winner] = 1.0
        return result

    def render(self, state: GameState) -> str:
        turn = "terminal" if self.is_terminal(state) else PLAYER_NAMES[state.player]
        winner = "none" if state.winner is None else PLAYER_NAMES[state.winner]
        win_type = state.win_type or "none"
        lines = [
            f"turn={turn} move={state.move_number} winner={winner} win={win_type}",
            f"stones_remaining red={state.stones_remaining[RED]} black={state.stones_remaining[BLACK]}",
            "rows=q-increasing",
        ]
        for r, row in zip(ROW_VALUES, ROWS):
            cells = " ".join(PLAYER_SYMBOLS[state.board[index]] for index in row)
            lines.append(f"{_axis_label('r', r):>5} {' ' * abs(r)}{cells}")
        return "\n".join(lines)

    def action_to_name(self, action: int) -> str:
        if type(action) is not int or action < 0 or action >= POINT_COUNT:
            raise ValueError(f"Action out of range: {action!r}")
        return "place:" + _coord_name(BOARD_COORDS[action])

    def name_to_action(self, name: str) -> int:
        if not isinstance(name, str) or not name.startswith("place:"):
            raise ValueError(f"Bad action name: {name!r}")
        coord = _parse_coord_name(name[len("place:"):])
        if coord not in INDEX_BY_COORD:
            raise ValueError(f"Coordinate is not on the board: {coord!r}")
        return INDEX_BY_COORD[coord]


def _winning_forms(board: Board, player: int) -> Tuple[str, ...]:
    components = list(_player_components(board, player))
    forms: Set[str] = set()

    for component in components:
        corner_count = 0
        sides: Set[int] = set()
        for index in component:
            if index in CORNER_INDICES:
                corner_count += 1
            side = SIDE_BY_INDEX[index]
            if side is not None:
                sides.add(side)
        if corner_count >= 2:
            forms.add("bridge")
        if len(sides) >= 3:
            forms.add("fork")

    if any(_component_encloses_point(component) for component in components):
        forms.add("ring")

    return tuple(form for form in ("ring", "bridge", "fork") if form in forms)


def _player_components(board: Board, player: int) -> Tuple[Tuple[int, ...], ...]:
    seen: Set[int] = set()
    components: List[Tuple[int, ...]] = []
    for start, cell in enumerate(board):
        if cell != player or start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: List[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in NEIGHBORS[current]:
                if neighbor not in seen and board[neighbor] == player:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(component))
    return tuple(components)


def _component_encloses_point(component: Tuple[int, ...]) -> bool:
    # The page diagram shows the smallest ring surrounding one point. A component
    # with fewer than six stones cannot surround a board point in this graph.
    if len(component) < 6:
        return False
    blockers = set(component)
    for target in range(POINT_COUNT):
        if IS_BOUNDARY[target]:
            continue
        if _target_cut_off_from_boundary(blockers, target):
            return True
    return False


def _target_cut_off_from_boundary(blockers: Set[int], target: int) -> bool:
    visited: Set[int] = set()
    queue: Deque[int] = deque()

    for index in BOUNDARY_INDICES:
        if _blocks(blockers, index, target):
            continue
        visited.add(index)
        queue.append(index)

    while queue:
        current = queue.popleft()
        if current == target:
            return False
        for neighbor in NEIGHBORS[current]:
            if neighbor in visited or _blocks(blockers, neighbor, target):
                continue
            visited.add(neighbor)
            queue.append(neighbor)

    return True


def _blocks(blockers: Set[int], index: int, target: int) -> bool:
    return index != target and index in blockers
```