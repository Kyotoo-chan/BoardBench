"""Rulebook-derived implementation of Havannah.

Source rules used here (translated/summarized from the supplied rulebook):
- Two players: red and black; red starts.
- The board has 169 intersection points.
- Players alternate placing one stone of their colour on a free point; stones do not move.
- A player wins immediately by first making a ring, bridge, or fork.

Assumptions needed for a programmatic API:
- The colour draw is not modeled; player 0 is red and player 1 is black.
- The 169-point board is represented as a hexagonal triangular-lattice board with
  radius 7 (side length 8), which has exactly 169 points.
- The component list says there are 55 stones of each colour; this implementation
  treats that as a strict supply. If the side to move has no stone left (or no
  free point exists) and nobody has won, the game is a draw.
- The rulebook gives no coordinate labels, so stable axial coordinates (q, r) are
  used in action names, with signs encoded as p/n/z.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

Coord = Tuple[int, int]
Action = Coord

NUM_PLAYERS = 2
RED = 0
BLACK = 1
PLAYER_NAMES = ("red", "black")
PLAYER_TOKENS = ("R", "B")
BOARD_RADIUS = 7
STONE_SUPPLY = 55

_NEIGHBOR_DELTAS: Tuple[Coord, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass
class GameState:
    """Public state for Havannah.

    board maps occupied coordinates to player numbers: 0 for red, 1 for black.
    apply_action returns a fresh GameState and does not mutate the input state.
    """

    board: Dict[Coord, int] = field(default_factory=dict)
    to_play: int = RED
    move_number: int = 0
    winner: Optional[int] = None
    win_type: Optional[str] = None
    history: Tuple[Tuple[int, Coord], ...] = ()


class Game:
    """A small, self-contained Havannah engine."""

    def __init__(self) -> None:
        self.num_players = NUM_PLAYERS
        self.radius = BOARD_RADIUS
        self.stone_supply = STONE_SUPPLY
        self.coords: Tuple[Coord, ...] = tuple(self._make_coords(self.radius))
        self.coord_set: Set[Coord] = set(self.coords)
        self.corners: Tuple[Coord, ...] = (
            (self.radius, 0),
            (self.radius, -self.radius),
            (0, -self.radius),
            (-self.radius, 0),
            (-self.radius, self.radius),
            (0, self.radius),
        )
        self.corner_set: Set[Coord] = set(self.corners)
        self.corner_index = {coord: i for i, coord in enumerate(self.corners)}
        self.side_indices = {coord: self._side_indices_for(coord) for coord in self.coords}
        self.boundary_set: Set[Coord] = {
            coord for coord in self.coords if self._is_boundary(coord)
        }

    # ----- Required API -------------------------------------------------

    def initial_state(self) -> GameState:
        return GameState()

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        return state.to_play

    def legal_actions(self, state: GameState) -> List[Action]:
        if state.winner is not None:
            return []
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            return []
        if len(state.board) >= len(self.coords):
            return []
        return [coord for coord in self.coords if coord not in state.board]

    def apply_action(self, state: GameState, action: Union[Action, str]) -> GameState:
        if self.is_terminal(state):
            raise ValueError("cannot apply an action to a terminal state")

        coord = self._coerce_action(action)
        if coord not in self.coord_set:
            raise ValueError(f"action is outside the board: {coord!r}")
        if coord in state.board:
            raise ValueError(f"point is already occupied: {self._coord_label(coord)}")
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            raise ValueError(f"{PLAYER_NAMES[state.to_play]} has no stones left")

        player = state.to_play
        new_board = dict(state.board)
        new_board[coord] = player
        new_history = state.history + ((player, coord),)

        win_types = self._winning_figures(new_board, player)
        if win_types:
            return GameState(
                board=new_board,
                to_play=1 - player,
                move_number=state.move_number + 1,
                winner=player,
                win_type="+".join(win_types),
                history=new_history,
            )

        return GameState(
            board=new_board,
            to_play=1 - player,
            move_number=state.move_number + 1,
            winner=None,
            win_type=None,
            history=new_history,
        )

    def is_terminal(self, state: GameState) -> bool:
        if state.winner is not None:
            return True
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            return True
        if len(state.board) >= len(self.coords):
            return True
        return False

    def returns(self, state: GameState) -> List[float]:
        if state.winner is None:
            return [0.0, 0.0]
        return [1.0 if player == state.winner else -1.0 for player in range(NUM_PLAYERS)]

    def render(self, state: GameState) -> str:
        if state.winner is not None:
            status = f"terminal winner={PLAYER_NAMES[state.winner]} win={state.win_type}"
        elif self.is_terminal(state):
            status = "terminal draw"
        else:
            status = f"to_play={PLAYER_NAMES[state.to_play]}"

        red_count = self._player_stone_count(state.board, RED)
        black_count = self._player_stone_count(state.board, BLACK)
        lines = [
            f"Havannah radius={self.radius} points={len(self.coords)} move={state.move_number} {status}",
            f"counts red={red_count}/{self.stone_supply} black={black_count}/{self.stone_supply}",
            "legend R=red B=black .=empty; coordinates are axial q,r",
        ]

        for r in range(-self.radius, self.radius + 1):
            q_min, q_max = self._q_range_for_r(r)
            row_len = q_max - q_min + 1
            indent = " " * (2 * self.radius + 1 - row_len)
            cells = []
            for q in range(q_min, q_max + 1):
                owner = state.board.get((q, r))
                cells.append("." if owner is None else PLAYER_TOKENS[owner])
            lines.append(
                f"{indent}r{self._signed_label(r)} q{self._signed_label(q_min)}..q{self._signed_label(q_max)} | "
                + " ".join(cells)
            )
        return "\n".join(lines)

    def action_to_name(self, action: Union[Action, str]) -> str:
        coord = self._coerce_action(action)
        if coord not in self.coord_set:
            raise ValueError(f"action is outside the board: {coord!r}")
        q, r = coord
        return f"place:q{self._signed_label(q)}_r{self._signed_label(r)}"

    def name_to_action(self, name: str) -> Action:
        if not isinstance(name, str) or not name.startswith("place:q"):
            raise ValueError(f"not a canonical Havannah action name: {name!r}")
        rest = name[len("place:q") :]
        if "_r" not in rest:
            raise ValueError(f"not a canonical Havannah action name: {name!r}")
        q_text, r_text = rest.split("_r", 1)
        q = self._parse_signed_label(q_text)
        r = self._parse_signed_label(r_text)
        coord = (q, r)
        if coord not in self.coord_set:
            raise ValueError(f"action name is outside the board: {name!r}")
        if self.action_to_name(coord) != name:
            raise ValueError(f"non-canonical Havannah action name: {name!r}")
        return coord

    # ----- Board construction and names --------------------------------

    @staticmethod
    def _make_coords(radius: int) -> List[Coord]:
        coords: List[Coord] = []
        for r in range(-radius, radius + 1):
            q_min = max(-radius, -r - radius)
            q_max = min(radius, -r + radius)
            for q in range(q_min, q_max + 1):
                coords.append((q, r))
        return coords

    def _q_range_for_r(self, r: int) -> Tuple[int, int]:
        return max(-self.radius, -r - self.radius), min(self.radius, -r + self.radius)

    @staticmethod
    def _signed_label(value: int) -> str:
        if value == 0:
            return "z0"
        if value > 0:
            return f"p{value}"
        return f"n{-value}"

    @staticmethod
    def _parse_signed_label(text: str) -> int:
        if len(text) < 2 or text[0] not in "pnz" or not text[1:].isdigit():
            raise ValueError(f"bad signed coordinate label: {text!r}")
        value = int(text[1:])
        if text[0] == "z":
            if value != 0:
                raise ValueError(f"zero coordinate must be z0, not {text!r}")
            return 0
        if value == 0:
            raise ValueError(f"non-zero coordinate label cannot use zero: {text!r}")
        return value if text[0] == "p" else -value

    def _coord_label(self, coord: Coord) -> str:
        return f"q{self._signed_label(coord[0])}_r{self._signed_label(coord[1])}"

    def _coerce_action(self, action: Union[Action, str]) -> Action:
        if isinstance(action, str):
            return self.name_to_action(action)
        if (
            isinstance(action, tuple)
            and len(action) == 2
            and isinstance(action[0], int)
            and isinstance(action[1], int)
        ):
            return action
        raise ValueError(f"action must be a coordinate tuple or canonical name: {action!r}")

    # ----- Geometry ------------------------------------------------------

    def _neighbors(self, coord: Coord) -> Iterable[Coord]:
        q, r = coord
        for dq, dr in _NEIGHBOR_DELTAS:
            neighbor = (q + dq, r + dr)
            if neighbor in self.coord_set:
                yield neighbor

    def _is_boundary(self, coord: Coord) -> bool:
        q, r = coord
        s = q + r
        return (
            abs(q) == self.radius
            or abs(r) == self.radius
            or abs(s) == self.radius
        )

    def _side_indices_for(self, coord: Coord) -> Tuple[int, ...]:
        """Return side indices touched by coord; corners deliberately return ()."""
        if coord in self.corner_set:
            return ()
        q, r = coord
        s = q + r
        sides: List[int] = []
        if q == self.radius:
            sides.append(0)
        if r == -self.radius:
            sides.append(1)
        if s == -self.radius:
            sides.append(2)
        if q == -self.radius:
            sides.append(3)
        if r == self.radius:
            sides.append(4)
        if s == self.radius:
            sides.append(5)
        return tuple(sides)

    # ----- Win detection -------------------------------------------------

    def _winning_figures(self, board: Dict[Coord, int], player: int) -> List[str]:
        wins: List[str] = []
        bridge, fork = self._bridge_and_fork(board, player)
        if self._has_ring(board, player):
            wins.append("ring")
        if bridge:
            wins.append("bridge")
        if fork:
            wins.append("fork")
        return wins

    def _bridge_and_fork(self, board: Dict[Coord, int], player: int) -> Tuple[bool, bool]:
        stones = {coord for coord, owner in board.items() if owner == player}
        unseen = set(stones)
        bridge = False
        fork = False

        while unseen:
            start = unseen.pop()
            stack = [start]
            corners_touched: Set[int] = set()
            sides_touched: Set[int] = set()

            while stack:
                coord = stack.pop()
                if coord in self.corner_index:
                    corners_touched.add(self.corner_index[coord])
                sides_touched.update(self.side_indices[coord])

                for neighbor in self._neighbors(coord):
                    if neighbor in unseen and board.get(neighbor) == player:
                        unseen.remove(neighbor)
                        stack.append(neighbor)

            if len(corners_touched) >= 2:
                bridge = True
            if len(sides_touched) >= 3:
                fork = True
            if bridge and fork:
                break

        return bridge, fork

    def _has_ring(self, board: Dict[Coord, int], player: int) -> bool:
        """Detect a closed connection enclosing at least one board point.

        A point is enclosed if, after treating the player's other stones as
        blockers, that point cannot reach any board boundary point. This checks
        empty/opponent points and also own stones that may already occupy the
        interior, matching the rulebook note that enclosed points may be occupied
        by anyone.
        """
        player_stones = {coord for coord, owner in board.items() if owner == player}
        if len(player_stones) < 6:
            return False

        for point in self.coords:
            if point in self.boundary_set:
                continue
            blocked = player_stones - ({point} if point in player_stones else set())
            if not self._can_reach_boundary(point, blocked):
                return True
        return False

    def _can_reach_boundary(self, start: Coord, blocked: Set[Coord]) -> bool:
        if start in blocked:
            return False
        if start in self.boundary_set:
            return True

        seen = {start}
        stack = [start]
        while stack:
            coord = stack.pop()
            for neighbor in self._neighbors(coord):
                if neighbor in blocked or neighbor in seen:
                    continue
                if neighbor in self.boundary_set:
                    return True
                seen.add(neighbor)
                stack.append(neighbor)
        return False

    @staticmethod
    def _player_stone_count(board: Dict[Coord, int], player: int) -> int:
        return sum(1 for owner in board.values() if owner == player)
