"""Conect, implemented from the supplied rule text.

The rule text gives the turn order, placement rule, edge ownership, and three
win conditions, but it does not specify an exact finite board size or coordinate
labels. This module therefore uses the ordinary hexagonal explanatory board
mentioned in the text, with a configurable radius and a default radius of 3.
The single perimeter is split into red and blue arcs with two shared edge cells.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, Union


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

RED = 0
BLUE = 1
PLAYERS = ("Red", "Blue")

Cell = Tuple[int, int]
Action = Cell
Stone = Tuple[int, int, int]

_NEIGHBOR_DELTAS: Tuple[Cell, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass(frozen=True)
class GameState:
    """Immutable public state for a Conect position.

    `stones` is a sorted tuple of `(q, r, player)` entries in axial hex
    coordinates. Player 0 is Red and player 1 is Blue.
    """

    board_radius: int = 3
    stones: Tuple[Stone, ...] = ()
    to_move: int = RED
    winner: Optional[int] = None
    move_count: int = 0
    history: Tuple[str, ...] = ()
    terminal_reason: str = ""


class Game:
    """A small, deterministic API for Conect."""

    def __init__(self, board_radius: int = 3):
        if not isinstance(board_radius, int) or board_radius < 1:
            raise ValueError("board_radius must be an integer >= 1")

        self.board_radius = board_radius
        self.num_players = 2
        self.players = PLAYERS
        self.center: Cell = (0, 0)
        self.cells: Tuple[Cell, ...] = tuple(
            sorted(self._make_cells(board_radius), key=self._cell_sort_key)
        )
        self.cell_set: FrozenSet[Cell] = frozenset(self.cells)
        self.perimeter: Tuple[Cell, ...] = tuple(self._make_perimeter(board_radius))
        self.edge_set: FrozenSet[Cell] = frozenset(self.perimeter)

        split = 3 * board_radius
        red_path = self.perimeter[: split + 1]
        blue_path = self.perimeter[split:] + (self.perimeter[0],)

        self.shared_edge_cells: Tuple[Cell, Cell] = (
            self.perimeter[0],
            self.perimeter[split],
        )
        self.edge_paths = {RED: red_path, BLUE: blue_path}
        self.edge_cells = {
            RED: frozenset(red_path),
            BLUE: frozenset(blue_path),
        }
        self._edge_path_positions = {
            RED: {cell: i for i, cell in enumerate(red_path)},
            BLUE: {cell: i for i, cell in enumerate(blue_path)},
        }

    def initial_state(self) -> GameState:
        return GameState(board_radius=self.board_radius)

    def current_player(self, state: GameState) -> int:
        self._validate_state(state)
        if self.is_terminal(state):
            return TERMINAL
        return state.to_move

    def legal_actions(self, state: GameState) -> List[Action]:
        self._validate_state(state)
        if self.is_terminal(state):
            return []
        occupied = set(self._board_map(state))
        return [cell for cell in self.cells if cell not in occupied]

    def apply_action(self, state: GameState, action: Union[Action, str]) -> GameState:
        self._validate_state(state)
        if isinstance(action, str):
            action = self.name_to_action(action)
        else:
            action = self._coerce_action(action)

        legal = set(self.legal_actions(state))
        if action not in legal:
            raise ValueError(f"illegal action: {self.action_to_name(action)}")

        board = self._board_map(state)
        player = state.to_move
        board[action] = player

        condition = self._winning_condition(board, player)
        if condition is not None:
            winner: Optional[int] = player
            terminal_reason = f"win:{condition}"
            next_player = player
        elif len(board) == len(self.cells):
            winner = None
            terminal_reason = "draw:board-full"
            next_player = 1 - player
        else:
            winner = None
            terminal_reason = ""
            next_player = 1 - player

        action_name = self.action_to_name(action)
        return GameState(
            board_radius=self.board_radius,
            stones=self._stones_from_board(board),
            to_move=next_player,
            winner=winner,
            move_count=state.move_count + 1,
            history=state.history + (action_name,),
            terminal_reason=terminal_reason,
        )

    def is_terminal(self, state: GameState) -> bool:
        self._validate_state(state)
        return state.winner is not None or len(state.stones) == len(self.cells)

    def returns(self, state: GameState) -> List[float]:
        self._validate_state(state)
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLUE:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def render(self, state: GameState) -> str:
        self._validate_state(state)
        board = self._board_map(state)
        if self.is_terminal(state):
            status = "terminal"
        else:
            status = f"turn={PLAYERS[state.to_move]}"

        winner = "none" if state.winner is None else PLAYERS[state.winner]
        reason = state.terminal_reason or "none"
        lines = [
            (
                f"Conect radius={self.board_radius} moves={state.move_count} "
                f"{status} winner={winner} reason={reason}"
            ),
            "key: first char .=empty/R=red/B=blue; suffix C=center r=red-edge b=blue-edge s=shared-edge _=inner",
        ]

        radius = self.board_radius
        for r in range(-radius, radius + 1):
            q_min = max(-radius, -r - radius)
            q_max = min(radius, -r + radius)
            row = [self._render_cell((q, r), board) for q in range(q_min, q_max + 1)]
            lines.append(f"r{self._signed_token(r)}: " + " ".join(row))
        return "\n".join(lines)

    def action_to_name(self, action: Union[Action, str]) -> str:
        if isinstance(action, str):
            return self.action_to_name(self.name_to_action(action))
        cell = self._coerce_action(action)
        if cell not in self.cell_set:
            raise ValueError(f"action cell is outside the board: {cell!r}")
        return f"place:{self._cell_label(cell)}"

    def name_to_action(self, name: str) -> Action:
        if not isinstance(name, str) or not name.startswith("place:"):
            raise ValueError(f"not a canonical Conect action name: {name!r}")
        cell = self._parse_cell_label(name[len("place:") :])
        if cell not in self.cell_set:
            raise ValueError(f"action cell is outside the board: {name!r}")
        return cell

    @staticmethod
    def _make_cells(radius: int) -> List[Cell]:
        cells: List[Cell] = []
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                if max(abs(q), abs(r), abs(-q - r)) <= radius:
                    cells.append((q, r))
        return cells

    @staticmethod
    def _make_perimeter(radius: int) -> List[Cell]:
        q, r = -radius, 0
        perimeter: List[Cell] = []
        directions: Tuple[Cell, ...] = (
            (1, -1),
            (1, 0),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (0, -1),
        )
        for dq, dr in directions:
            for _ in range(radius):
                perimeter.append((q, r))
                q += dq
                r += dr
        return perimeter

    @staticmethod
    def _cell_sort_key(cell: Cell) -> Tuple[int, int]:
        q, r = cell
        return (r, q)

    def _validate_state(self, state: GameState) -> None:
        if not isinstance(state, GameState):
            raise TypeError("state must be a GameState")
        if state.board_radius != self.board_radius:
            raise ValueError("state board_radius does not match this Game")
        if state.to_move not in (RED, BLUE):
            raise ValueError("state.to_move must be RED/0 or BLUE/1")
        if state.winner not in (None, RED, BLUE):
            raise ValueError("state.winner must be None, RED/0, or BLUE/1")

        seen: Set[Cell] = set()
        for q, r, player in state.stones:
            cell = (q, r)
            if cell not in self.cell_set:
                raise ValueError(f"stone outside board: {cell!r}")
            if cell in seen:
                raise ValueError(f"duplicate stone cell: {cell!r}")
            if player not in (RED, BLUE):
                raise ValueError(f"invalid stone owner: {player!r}")
            seen.add(cell)

    def _board_map(self, state: GameState) -> Dict[Cell, int]:
        return {(q, r): player for q, r, player in state.stones}

    def _stones_from_board(self, board: Dict[Cell, int]) -> Tuple[Stone, ...]:
        return tuple(
            (q, r, board[(q, r)])
            for q, r in sorted(board.keys(), key=self._cell_sort_key)
        )

    def _coerce_action(self, action: object) -> Action:
        if (
            isinstance(action, tuple)
            and len(action) == 2
            and isinstance(action[0], int)
            and isinstance(action[1], int)
        ):
            return (action[0], action[1])
        raise ValueError(f"action must be a coordinate tuple like (q, r): {action!r}")

    def _neighbors(self, cell: Cell) -> Iterable[Cell]:
        q, r = cell
        for dq, dr in _NEIGHBOR_DELTAS:
            neighbor = (q + dq, r + dr)
            if neighbor in self.cell_set:
                yield neighbor

    def _winning_condition(self, board: Dict[Cell, int], player: int) -> Optional[str]:
        components = self._player_components(board, player)

        for component in components:
            if self._edge_loop_surrounds_center(component, player):
                return "edge-loop"

        for component in components:
            if (
                self.center not in component
                and component & self.edge_cells[player]
                and self._center_cut_off_by_barrier(component)
            ):
                return "surrounding-group"

        for component in components:
            if self.center in component and component & self.edge_cells[player]:
                return "center-path"

        return None

    def _player_components(self, board: Dict[Cell, int], player: int) -> List[FrozenSet[Cell]]:
        unvisited = {cell for cell, owner in board.items() if owner == player}
        components: List[FrozenSet[Cell]] = []

        while unvisited:
            start = unvisited.pop()
            component = {start}
            queue: Deque[Cell] = deque([start])
            while queue:
                cell = queue.popleft()
                for neighbor in self._neighbors(cell):
                    if neighbor in unvisited:
                        unvisited.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            components.append(frozenset(component))

        return components

    def _edge_loop_surrounds_center(self, component: FrozenSet[Cell], player: int) -> bool:
        if self.center in component:
            return False

        path = self.edge_paths[player]
        positions = self._edge_path_positions[player]
        touched = sorted(positions[cell] for cell in component if cell in positions)
        if len(touched) < 2:
            return False

        for i, start in enumerate(touched[:-1]):
            for end in touched[i + 1 :]:
                edge_segment = frozenset(path[start : end + 1])
                # The loop is the player's stone path plus the intervening edge
                # cells. It surrounds the center when that barrier separates the
                # center cell from every non-barrier perimeter cell.
                barrier = frozenset(set(component) | set(edge_segment))
                if self._center_cut_off_by_barrier(barrier):
                    return True
        return False

    def _center_cut_off_by_barrier(self, barrier: FrozenSet[Cell]) -> bool:
        if self.center in barrier:
            return False

        seen = {self.center}
        queue: Deque[Cell] = deque([self.center])
        while queue:
            cell = queue.popleft()
            if cell in self.edge_set and cell not in barrier:
                return False
            for neighbor in self._neighbors(cell):
                if neighbor not in seen and neighbor not in barrier:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return True

    def _render_cell(self, cell: Cell, board: Dict[Cell, int]) -> str:
        owner = board.get(cell)
        if owner == RED:
            piece = "R"
        elif owner == BLUE:
            piece = "B"
        else:
            piece = "."

        if cell == self.center:
            suffix = "C"
        elif cell in self.edge_cells[RED] and cell in self.edge_cells[BLUE]:
            suffix = "s"
        elif cell in self.edge_cells[RED]:
            suffix = "r"
        elif cell in self.edge_cells[BLUE]:
            suffix = "b"
        else:
            suffix = "_"
        return piece + suffix

    @classmethod
    def _cell_label(cls, cell: Cell) -> str:
        q, r = cell
        return f"q{cls._signed_token(q)}_r{cls._signed_token(r)}"

    @classmethod
    def _parse_cell_label(cls, label: str) -> Cell:
        if not label.startswith("q"):
            raise ValueError(f"bad cell label: {label!r}")
        body = label[1:]
        parts = body.split("_r", 1)
        if len(parts) != 2:
            raise ValueError(f"bad cell label: {label!r}")
        return (cls._parse_signed_token(parts[0]), cls._parse_signed_token(parts[1]))

    @staticmethod
    def _signed_token(value: int) -> str:
        if value > 0:
            return f"pos{value}"
        if value < 0:
            return f"neg{-value}"
        return "zero"

    @staticmethod
    def _parse_signed_token(token: str) -> int:
        if token == "zero":
            return 0
        if token.startswith("pos") and token[3:].isdigit():
            return int(token[3:])
        if token.startswith("neg") and token[3:].isdigit():
            return -int(token[3:])
        raise ValueError(f"bad signed coordinate token: {token!r}")
