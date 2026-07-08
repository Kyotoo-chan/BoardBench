"""Self-contained implementation of Conect from the supplied rule text.

The rule sheet describes the game topologically and illustrates wins on an
"ordinary hexagonal board", but it does not give coordinate labels, a fixed
board size, or a machine-readable conical projection.  This module therefore
uses the illustrated ordinary hexagonal board as the playable model: a hex board
of side length 4 by default, with the perimeter divided into two opposite arcs
(Red and Blue) sharing the two arc end cells.
"""

from dataclasses import dataclass
import re
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

Coord = Tuple[int, int]
Action = Coord

EMPTY = -1
RED = 0
BLUE = 1
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

_PLAYER_NAMES = ("Red", "Blue")
_NEIGHBOR_STEPS: Tuple[Coord, ...] = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (1, -1),
    (-1, 1),
)
_ACTION_RE = re.compile(r"^place:q(0|p[1-9]\d*|n[1-9]\d*)_r(0|p[1-9]\d*|n[1-9]\d*)$")


@dataclass(frozen=True)
class GameState:
    """Complete public state for this perfect-information placement game."""

    board: Tuple[int, ...]
    to_move: int = RED
    terminal: bool = False
    winner: Optional[int] = None
    move_number: int = 0
    history: Tuple[str, ...] = ()
    win_reason: str = ""


class Game:
    """Conect on an ordinary hexagonal board.

    Assumptions from incomplete rule text:
    * The default board is the side-length-4 hexagon shown in Figures 1--3.
      A different side length may be supplied for experiments.
    * Red's edge is one half of the perimeter and Blue's edge is the opposite
      half; the two end cells of those arcs are shared and belong to both
      players, as stated by the rules.
    * "Surrounds the center" is implemented as graph separation: a set of
      player's cells (plus, for edge-path wins, the relevant edge interval)
      surrounds the center iff the center cell cannot reach any unblocked
      perimeter cell through cells not in that set.
    """

    num_players = 2
    player_names = _PLAYER_NAMES

    def __init__(self, side_length: int = 4):
        if not isinstance(side_length, int) or side_length < 2:
            raise ValueError("side_length must be an integer at least 2")
        self.side_length = side_length
        self.radius = side_length - 1
        self.center: Coord = (0, 0)

        coords = self._make_hex_coords(self.radius)
        self.coords: Tuple[Coord, ...] = tuple(sorted(coords, key=lambda c: (c[1], c[0])))
        self._index: Dict[Coord, int] = {coord: i for i, coord in enumerate(self.coords)}
        self._neighbors: Dict[Coord, Tuple[Coord, ...]] = {
            coord: tuple(
                (coord[0] + dq, coord[1] + dr)
                for dq, dr in _NEIGHBOR_STEPS
                if (coord[0] + dq, coord[1] + dr) in self._index
            )
            for coord in self.coords
        }

        self.boundary: FrozenSet[Coord] = frozenset(
            coord for coord in self.coords if self._hex_distance(coord) == self.radius
        )
        perimeter = self._make_perimeter(self.radius)
        self.perimeter: Tuple[Coord, ...] = perimeter

        # Start at one shared cell, walk three perimeter sides to the opposite
        # shared cell for Red, and use the remaining three sides for Blue.
        split = 3 * self.radius
        red_path = perimeter[: split + 1]
        blue_path = perimeter[split:] + perimeter[:1]
        self.edge_paths: Dict[int, Tuple[Coord, ...]] = {RED: red_path, BLUE: blue_path}
        self.edges: Dict[int, FrozenSet[Coord]] = {
            RED: frozenset(red_path),
            BLUE: frozenset(blue_path),
        }
        self.shared_edge_cells: FrozenSet[Coord] = frozenset((perimeter[0], perimeter[split]))
        self._edge_positions: Dict[int, Dict[Coord, int]] = {
            player: {coord: i for i, coord in enumerate(path)}
            for player, path in self.edge_paths.items()
        }

    # ----- Public API -----

    def initial_state(self) -> GameState:
        return GameState(board=(EMPTY,) * len(self.coords), to_move=RED)

    def current_player(self, state: GameState) -> int:
        return TERMINAL if state.terminal else state.to_move

    def legal_actions(self, state: GameState) -> List[Action]:
        if state.terminal:
            return []
        return [coord for coord in self.coords if state.board[self._index[coord]] == EMPTY]

    def apply_action(self, state: GameState, action: Action) -> GameState:
        """Return a fresh state after placing the current player's stone."""
        if state.terminal:
            raise ValueError("cannot apply an action to a terminal state")
        coord = self._normalize_action(action)
        if coord not in self._index:
            raise ValueError(f"unknown cell: {coord!r}")
        idx = self._index[coord]
        if state.board[idx] != EMPTY:
            raise ValueError(f"cell is already occupied: {self._coord_label(coord)}")

        player = state.to_move
        board = list(state.board)
        board[idx] = player
        new_board = tuple(board)
        reasons = self._winning_reasons(new_board, player)
        terminal = bool(reasons)
        winner: Optional[int] = player if terminal else None
        win_reason = "+".join(reasons)

        if not terminal and all(v != EMPTY for v in new_board):
            terminal = True
            win_reason = "draw-board-full"

        next_player = player if terminal else 1 - player
        name = self.action_to_name(coord)
        return GameState(
            board=new_board,
            to_move=next_player,
            terminal=terminal,
            winner=winner,
            move_number=state.move_number + 1,
            history=state.history + (name,),
            win_reason=win_reason,
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> List[float]:
        if not state.terminal or state.winner is None:
            return [0.0, 0.0]
        return [1.0, -1.0] if state.winner == RED else [-1.0, 1.0]

    def render(self, state: GameState) -> str:
        status = "terminal" if state.terminal else f"turn={_PLAYER_NAMES[state.to_move]}"
        winner = "none" if state.winner is None else _PLAYER_NAMES[state.winner]
        lines = [
            f"Conect(side={self.side_length}, move={state.move_number}, {status}, winner={winner}, reason={state.win_reason or '-'})",
            "legend: R/B stones, r=empty Red edge, b=empty Blue edge, s=empty shared edge, c=empty center, .=empty interior",
        ]
        m = self.radius
        for r in range(-m, m + 1):
            q_min = max(-m, -r - m)
            q_max = min(m, -r + m)
            cells = []
            for q in range(q_min, q_max + 1):
                coord = (q, r)
                cells.append(self._render_cell(state.board, coord))
            indent = " " * (m - (q_max - q_min))
            lines.append(f"r={self._signed(r):>2} {indent}" + " ".join(cells))
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        coord = self._normalize_action(action)
        if coord not in self._index:
            raise ValueError(f"unknown cell: {coord!r}")
        return "place:" + self._coord_label(coord)

    def name_to_action(self, name: str) -> Action:
        if not isinstance(name, str):
            raise ValueError("action name must be a string")
        match = _ACTION_RE.match(name)
        if not match:
            raise ValueError(f"not a canonical Conect action name: {name!r}")
        coord = (self._parse_signed(match.group(1)), self._parse_signed(match.group(2)))
        if coord not in self._index:
            raise ValueError(f"action name refers to a cell outside this board: {name!r}")
        return coord

    # ----- Board construction and labels -----

    @staticmethod
    def _make_hex_coords(radius: int) -> Set[Coord]:
        return {
            (q, r)
            for q in range(-radius, radius + 1)
            for r in range(-radius, radius + 1)
            if max(abs(q), abs(r), abs(q + r)) <= radius
        }

    @staticmethod
    def _hex_distance(coord: Coord) -> int:
        q, r = coord
        return max(abs(q), abs(r), abs(q + r))

    @staticmethod
    def _make_perimeter(radius: int) -> Tuple[Coord, ...]:
        start = (radius, -radius)
        coord = start
        order = [coord]
        # Clockwise around the six sides of the axial-coordinate hexagon.
        for dq, dr in ((0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)):
            for _ in range(radius):
                coord = (coord[0] + dq, coord[1] + dr)
                if coord != start:
                    order.append(coord)
        return tuple(order)

    @classmethod
    def _signed(cls, value: int) -> str:
        if value == 0:
            return "0"
        return ("p" if value > 0 else "n") + str(abs(value))

    @classmethod
    def _parse_signed(cls, text: str) -> int:
        if text == "0":
            return 0
        if text[0] == "p":
            return int(text[1:])
        if text[0] == "n":
            return -int(text[1:])
        raise ValueError(f"bad signed coordinate component: {text!r}")

    @classmethod
    def _coord_label(cls, coord: Coord) -> str:
        return f"q{cls._signed(coord[0])}_r{cls._signed(coord[1])}"

    def _normalize_action(self, action: Action) -> Coord:
        if isinstance(action, str):
            return self.name_to_action(action)
        if (
            isinstance(action, tuple)
            and len(action) == 2
            and isinstance(action[0], int)
            and isinstance(action[1], int)
        ):
            return action
        raise ValueError(f"action must be a coordinate tuple or canonical name, got {action!r}")

    def _render_cell(self, board: Tuple[int, ...], coord: Coord) -> str:
        value = board[self._index[coord]]
        if value == RED:
            return "R"
        if value == BLUE:
            return "B"
        if coord == self.center:
            return "c"
        in_red = coord in self.edges[RED]
        in_blue = coord in self.edges[BLUE]
        if in_red and in_blue:
            return "s"
        if in_red:
            return "r"
        if in_blue:
            return "b"
        return "."

    # ----- Win detection -----

    def _winning_reasons(self, board: Tuple[int, ...], player: int) -> List[str]:
        reasons = []
        if self._wins_by_edge_loop(board, player):
            reasons.append("edge-loop")
        if self._wins_by_surrounding_group(board, player):
            reasons.append("surround-center")
        if self._wins_by_center_path(board, player):
            reasons.append("center-path")
        return reasons

    def _player_cells(self, board: Tuple[int, ...], player: int) -> Set[Coord]:
        return {coord for coord in self.coords if board[self._index[coord]] == player}

    def _components(self, cells: Iterable[Coord]) -> List[Set[Coord]]:
        unseen = set(cells)
        components: List[Set[Coord]] = []
        while unseen:
            start = unseen.pop()
            comp = {start}
            stack = [start]
            while stack:
                cur = stack.pop()
                for nbr in self._neighbors[cur]:
                    if nbr in unseen:
                        unseen.remove(nbr)
                        comp.add(nbr)
                        stack.append(nbr)
            components.append(comp)
        return components

    def _wins_by_center_path(self, board: Tuple[int, ...], player: int) -> bool:
        if board[self._index[self.center]] != player:
            return False
        player_cells = self._player_cells(board, player)
        for comp in self._components(player_cells):
            if self.center in comp:
                return bool(comp & self.edges[player])
        return False

    def _wins_by_surrounding_group(self, board: Tuple[int, ...], player: int) -> bool:
        player_cells = self._player_cells(board, player)
        for comp in self._components(player_cells):
            # A group occupying the center is handled by the center-path rule;
            # "surrounds the center cell" is treated as enclosing it from outside.
            if self.center in comp:
                continue
            if comp & self.edges[player] and self._separates_center(comp):
                return True
        return False

    def _wins_by_edge_loop(self, board: Tuple[int, ...], player: int) -> bool:
        player_cells = self._player_cells(board, player)
        edge_path = self.edge_paths[player]
        edge_pos = self._edge_positions[player]
        for comp in self._components(player_cells):
            touched_positions = sorted(edge_pos[c] for c in comp if c in edge_pos)
            if len(touched_positions) < 2:
                continue
            for i, start_pos in enumerate(touched_positions[:-1]):
                for end_pos in touched_positions[i + 1 :]:
                    interval = set(edge_path[start_pos : end_pos + 1])
                    barrier = set(comp) | interval
                    # The path plus the intervening own-edge cells must make a
                    # loop around the center, not merely touch the perimeter.
                    if self.center not in barrier and self._separates_center(barrier):
                        return True
        return False

    def _separates_center(self, blocked: Iterable[Coord]) -> bool:
        """Whether blocked cells keep the center from reaching the perimeter."""
        blocked_set = set(blocked)
        if self.center in blocked_set:
            return False
        seen = {self.center}
        stack = [self.center]
        while stack:
            cur = stack.pop()
            if cur in self.boundary and cur not in blocked_set:
                return False
            for nbr in self._neighbors[cur]:
                if nbr not in blocked_set and nbr not in seen:
                    seen.add(nbr)
                    stack.append(nbr)
        return True


__all__ = [
    "Action",
    "BLUE",
    "CHANCE",
    "Coord",
    "EMPTY",
    "Game",
    "GameState",
    "RED",
    "SIMULTANEOUS",
    "TERMINAL",
]
