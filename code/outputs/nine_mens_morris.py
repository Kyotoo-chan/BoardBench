"""
Open questions / assumptions

This implementation uses only the supplied rule text. The text describes the
mechanics of Muehle / Nine Men's Morris, but it does not include the actual
board diagram: the number of points, their names, the adjacency graph, and the
exact triples that count as rows are unspecified.

To keep the file executable, Game() therefore uses an explicit abstract default
board: a 24-point 4x6 grid named r1c1 .. r4c6. Adjacent points are orthogonal
grid neighbors. A mill is any consecutive horizontal or vertical triple on this
abstract grid. This is a documented assumption, not a claim that the omitted
Muehleplan has this geometry. If the real board diagram is provided later,
Game can be constructed with custom point_names, mill_lines, and adjacency.

Other rule assumptions:
- White is player 0, black is player 1, and white starts.
- A capture is caused only by a newly closed mill, not by a mill that was
  already closed before the action.
- If one action closes multiple mills, only one opposing stone is removed,
  because the text says "einen" stone.
- A removable stone may not be part of any currently closed mill. If every
  opposing stone is protected this way, no stone is removed, except for the
  special jumper rule.
- A player is a jumper only after the placing phase is over and exactly three
  of that player's stones remain on the board.
- No draw, repetition, or move-limit rule is given, so none is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union

EMPTY = -1
WHITE = 0
BLACK = 1
PLAYERS = (WHITE, BLACK)
PLAYER_NAMES = ("white", "black")
DEFAULT_STONES_PER_PLAYER = 9

# Abstract assumed board geometry. See the module docstring.
DEFAULT_ROWS = 4
DEFAULT_COLS = 6


def _grid_index(row: int, col: int) -> int:
    return row * DEFAULT_COLS + col


DEFAULT_POINT_NAMES = tuple(
    f"r{row + 1}c{col + 1}"
    for row in range(DEFAULT_ROWS)
    for col in range(DEFAULT_COLS)
)

DEFAULT_MILLS = tuple(
    (_grid_index(row, col), _grid_index(row, col + 1), _grid_index(row, col + 2))
    for row in range(DEFAULT_ROWS)
    for col in range(DEFAULT_COLS - 2)
) + tuple(
    (_grid_index(row, col), _grid_index(row + 1, col), _grid_index(row + 2, col))
    for col in range(DEFAULT_COLS)
    for row in range(DEFAULT_ROWS - 2)
)


def _make_grid_adjacency(
    rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS
) -> Tuple[Tuple[int, ...], ...]:
    neighbors: List[Set[int]] = [set() for _ in range(rows * cols)]

    def index(row: int, col: int) -> int:
        return row * cols + col

    for row in range(rows):
        for col in range(cols):
            here = index(row, col)
            if row > 0:
                neighbors[here].add(index(row - 1, col))
            if row + 1 < rows:
                neighbors[here].add(index(row + 1, col))
            if col > 0:
                neighbors[here].add(index(row, col - 1))
            if col + 1 < cols:
                neighbors[here].add(index(row, col + 1))
    return tuple(tuple(sorted(items)) for items in neighbors)


DEFAULT_ADJACENCY = _make_grid_adjacency()


@dataclass(frozen=True)
class Action:
    """A complete turn action, including any removal choice after a mill."""

    kind: str  # "place" or "move"
    source: Optional[int]
    destination: int
    remove: Optional[int] = None
    wins_by_mill: bool = False


@dataclass(frozen=True)
class GameState:
    """Immutable public game state."""

    board: Tuple[int, ...]
    to_place: Tuple[int, int]
    current: int = WHITE
    winner: Optional[int] = None
    move_number: int = 0


class Game:
    """Simple self-contained game API for the supplied rule text."""

    def __init__(
        self,
        point_names: Optional[Sequence[str]] = None,
        mill_lines: Optional[Sequence[Sequence[object]]] = None,
        adjacency: Optional[Sequence[Sequence[object]]] = None,
        stones_per_player: int = DEFAULT_STONES_PER_PLAYER,
    ) -> None:
        self.point_names = tuple(DEFAULT_POINT_NAMES if point_names is None else point_names)
        self.num_points = len(self.point_names)
        if self.num_points <= 0:
            raise ValueError("the board must contain at least one point")
        if len(set(self.point_names)) != self.num_points:
            raise ValueError("point names must be unique")
        for name in self.point_names:
            if not isinstance(name, str) or not name:
                raise ValueError("each point name must be a non-empty string")
            if ":" in name or "/" in name or "->" in name:
                raise ValueError("point names may not contain ':', '/', or '->'")

        self._point_to_index: Dict[str, int] = {
            name: index for index, name in enumerate(self.point_names)
        }
        self.stones_per_player = int(stones_per_player)
        if self.stones_per_player <= 0:
            raise ValueError("stones_per_player must be positive")

        raw_mills = DEFAULT_MILLS if mill_lines is None else mill_lines
        mills: List[Tuple[int, int, int]] = []
        for line in raw_mills:
            converted = tuple(self._coerce_index(item) for item in line)
            if len(converted) != 3:
                raise ValueError("each mill line must contain exactly three points")
            if len(set(converted)) != 3:
                raise ValueError("a mill line must contain three distinct points")
            mills.append((converted[0], converted[1], converted[2]))
        if not mills:
            raise ValueError("at least one mill line is required")
        self.mill_lines = tuple(mills)

        raw_adjacency = DEFAULT_ADJACENCY if adjacency is None else adjacency
        if len(raw_adjacency) != self.num_points:
            raise ValueError("adjacency must have one entry per point")
        neighbor_sets: List[Set[int]] = [set() for _ in range(self.num_points)]
        for index, neighbors in enumerate(raw_adjacency):
            for item in neighbors:
                neighbor = self._coerce_index(item)
                if neighbor == index:
                    raise ValueError("a point may not be adjacent to itself")
                neighbor_sets[index].add(neighbor)
                neighbor_sets[neighbor].add(index)
        self.adjacency = tuple(tuple(sorted(items)) for items in neighbor_sets)

    def initial_state(self) -> GameState:
        return GameState(
            board=(EMPTY,) * self.num_points,
            to_place=(self.stones_per_player, self.stones_per_player),
            current=WHITE,
            winner=None,
            move_number=0,
        )

    def current_player(self, state: GameState) -> int:
        """Return the current player, or -1 if the state is terminal."""
        return -1 if self.is_terminal(state) else state.current

    def legal_actions(self, state: GameState) -> List[Action]:
        if self._winner_without_no_move(state) is not None:
            return []
        actions = list(self._legal_actions_no_terminal(state))
        return sorted(actions, key=self.action_to_name)

    def apply_action(self, state: GameState, action: Union[Action, str]) -> GameState:
        """Return the next state. The input state is not mutated."""
        if isinstance(action, str):
            action = self.name_to_action(action)
        if not isinstance(action, Action):
            raise TypeError("action must be an Action or canonical action name")
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action!r}")

        player = state.current
        opponent = 1 - player
        board = list(state.board)
        to_place = list(state.to_place)
        winner: Optional[int] = None

        if action.kind == "place":
            board[action.destination] = player
            to_place[player] -= 1
        elif action.kind == "move":
            if action.source is None:
                raise ValueError("move action is missing a source point")
            board[action.source] = EMPTY
            board[action.destination] = player
        else:
            raise ValueError(f"unknown action kind: {action.kind!r}")

        if action.wins_by_mill:
            # Special rule: if the opponent is a jumper and a mill is closed,
            # the jumper immediately loses all three stones, even in a mill.
            for index, value in enumerate(board):
                if value == opponent:
                    board[index] = EMPTY
            winner = player
        elif action.remove is not None:
            board[action.remove] = EMPTY

        next_state = GameState(
            board=tuple(board),
            to_place=(to_place[WHITE], to_place[BLACK]),
            current=opponent,
            winner=winner,
            move_number=state.move_number + 1,
        )
        computed_winner = self._winner(next_state)
        if computed_winner is not None:
            next_state = GameState(
                board=next_state.board,
                to_place=next_state.to_place,
                current=next_state.current,
                winner=computed_winner,
                move_number=next_state.move_number,
            )
        return next_state

    def is_terminal(self, state: GameState) -> bool:
        return self._winner(state) is not None

    def returns(self, state: GameState) -> List[float]:
        winner = self._winner(state)
        if winner is None:
            return [0.0, 0.0]
        return [1.0 if player == winner else -1.0 for player in PLAYERS]

    def render(self, state: GameState) -> str:
        winner = self._winner(state)
        phase = "placing" if self._placing_phase(state) else "moving"
        current = "terminal" if winner is not None else PLAYER_NAMES[state.current]
        winner_name = "none" if winner is None else PLAYER_NAMES[winner]
        on_board = (
            f"white:{self._board_count(state.board, WHITE)} "
            f"black:{self._board_count(state.board, BLACK)}"
        )
        to_place = f"white:{state.to_place[WHITE]} black:{state.to_place[BLACK]}"

        board_items = []
        for index, name in enumerate(self.point_names):
            value = state.board[index]
            if value == WHITE:
                marker = "W"
            elif value == BLACK:
                marker = "B"
            else:
                marker = "."
            board_items.append(f"{name}={marker}")

        return "\n".join(
            [
                "game=nine_mens_morris",
                f"move_number={state.move_number}",
                f"phase={phase}",
                f"current={current}",
                f"winner={winner_name}",
                f"to_place={to_place}",
                f"on_board={on_board}",
                "board=" + " ".join(board_items),
            ]
        )

    def action_to_name(self, action: Action) -> str:
        if action.kind == "place":
            parts = [f"place:{self._index_to_name(action.destination)}"]
        elif action.kind == "move":
            if action.source is None:
                raise ValueError("move action is missing a source point")
            parts = [
                f"move:{self._index_to_name(action.source)}"
                f"->{self._index_to_name(action.destination)}"
            ]
        else:
            raise ValueError(f"unknown action kind: {action.kind!r}")

        if action.remove is not None:
            parts.append(f"remove:{self._index_to_name(action.remove)}")
        if action.wins_by_mill:
            parts.append("win")
        return "/".join(parts)

    def name_to_action(self, name: str) -> Action:
        if not isinstance(name, str) or not name:
            raise ValueError("action name must be a non-empty string")
        parts = name.split("/")
        head = parts[0]
        remove: Optional[int] = None
        wins_by_mill = False

        for suffix in parts[1:]:
            if suffix == "win":
                if wins_by_mill:
                    raise ValueError(f"duplicate win suffix in action name: {name!r}")
                wins_by_mill = True
            elif suffix.startswith("remove:"):
                if remove is not None:
                    raise ValueError(f"duplicate remove suffix in action name: {name!r}")
                remove = self._name_to_index(suffix[len("remove:") :])
            else:
                raise ValueError(f"unknown action suffix: {suffix!r}")

        if head.startswith("place:"):
            destination = self._name_to_index(head[len("place:") :])
            return Action("place", None, destination, remove, wins_by_mill)

        if head.startswith("move:"):
            route = head[len("move:") :]
            if "->" not in route:
                raise ValueError(f"move action is missing '->': {name!r}")
            source_text, destination_text = route.split("->", 1)
            source = self._name_to_index(source_text)
            destination = self._name_to_index(destination_text)
            return Action("move", source, destination, remove, wins_by_mill)

        raise ValueError(f"unknown action name: {name!r}")

    def _coerce_index(self, value: object) -> int:
        if isinstance(value, str):
            return self._name_to_index(value)
        try:
            index = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError(f"invalid point index: {value!r}") from None
        if index < 0 or index >= self.num_points:
            raise ValueError(f"point index out of range: {index!r}")
        return index

    def _index_to_name(self, index: int) -> str:
        if index < 0 or index >= self.num_points:
            raise ValueError(f"point index out of range: {index!r}")
        return self.point_names[index]

    def _name_to_index(self, name: str) -> int:
        try:
            return self._point_to_index[name]
        except KeyError:
            raise ValueError(f"unknown point name: {name!r}") from None

    def _placing_phase(self, state: GameState) -> bool:
        return any(count > 0 for count in state.to_place)

    def _board_count(self, board: Tuple[int, ...], player: int) -> int:
        return sum(1 for value in board if value == player)

    def _total_available(self, state: GameState, player: int) -> int:
        return self._board_count(state.board, player) + state.to_place[player]

    def _is_jumper(self, state: GameState, player: int) -> bool:
        return (not self._placing_phase(state)) and self._board_count(state.board, player) == 3

    def _winner_without_no_move(self, state: GameState) -> Optional[int]:
        if state.winner is not None:
            return state.winner
        white_total = self._total_available(state, WHITE)
        black_total = self._total_available(state, BLACK)
        if white_total <= 0 and black_total <= 0:
            return None
        if white_total <= 0:
            return BLACK
        if black_total <= 0:
            return WHITE
        return None

    def _winner(self, state: GameState) -> Optional[int]:
        winner = self._winner_without_no_move(state)
        if winner is not None:
            return winner
        if not any(self._legal_actions_no_terminal(state)):
            # End condition: a player wins if the opponent has no legal move.
            return 1 - state.current
        return None

    def _legal_actions_no_terminal(self, state: GameState) -> Iterator[Action]:
        if state.current not in PLAYERS:
            return
        if self._winner_without_no_move(state) is not None:
            return

        player = state.current
        if self._placing_phase(state):
            if state.to_place[player] <= 0:
                return
            for destination, value in enumerate(state.board):
                if value != EMPTY:
                    continue
                board = list(state.board)
                board[destination] = player
                yield from self._actions_after_board(
                    state, "place", None, destination, tuple(board)
                )
            return

        sources = [index for index, value in enumerate(state.board) if value == player]
        if not sources:
            return

        if self._is_jumper(state, player):
            destinations = [index for index, value in enumerate(state.board) if value == EMPTY]
            for source in sources:
                for destination in destinations:
                    board = list(state.board)
                    board[source] = EMPTY
                    board[destination] = player
                    yield from self._actions_after_board(
                        state, "move", source, destination, tuple(board)
                    )
        else:
            for source in sources:
                for destination in self.adjacency[source]:
                    if state.board[destination] != EMPTY:
                        continue
                    board = list(state.board)
                    board[source] = EMPTY
                    board[destination] = player
                    yield from self._actions_after_board(
                        state, "move", source, destination, tuple(board)
                    )

    def _actions_after_board(
        self,
        state: GameState,
        kind: str,
        source: Optional[int],
        destination: int,
        after_board: Tuple[int, ...],
    ) -> Iterator[Action]:
        player = state.current
        opponent = 1 - player
        newly_closed = self._newly_closed_mills(state.board, after_board, player)
        if not newly_closed:
            yield Action(kind, source, destination)
            return

        if self._is_jumper(state, opponent):
            yield Action(kind, source, destination, wins_by_mill=True)
            return

        removals = self._removable_stones(after_board, opponent)
        if removals:
            for remove in removals:
                yield Action(kind, source, destination, remove=remove)
        else:
            # The text forbids removing a stone from a closed mill and gives no
            # exception if all opposing stones are protected. Assumption: the
            # mill still closes, but no stone is removed.
            yield Action(kind, source, destination)

    def _closed_mills(self, board: Tuple[int, ...], player: int) -> Set[int]:
        closed: Set[int] = set()
        for index, line in enumerate(self.mill_lines):
            if all(board[position] == player for position in line):
                closed.add(index)
        return closed

    def _newly_closed_mills(
        self, before_board: Tuple[int, ...], after_board: Tuple[int, ...], player: int
    ) -> Set[int]:
        before = self._closed_mills(before_board, player)
        after = self._closed_mills(after_board, player)
        return after - before

    def _stones_in_closed_mills(self, board: Tuple[int, ...], player: int) -> Set[int]:
        protected: Set[int] = set()
        for line in self.mill_lines:
            if all(board[position] == player for position in line):
                protected.update(line)
        return protected

    def _removable_stones(self, board: Tuple[int, ...], player: int) -> Tuple[int, ...]:
        protected = self._stones_in_closed_mills(board, player)
        return tuple(
            index
            for index, value in enumerate(board)
            if value == player and index not in protected
        )
