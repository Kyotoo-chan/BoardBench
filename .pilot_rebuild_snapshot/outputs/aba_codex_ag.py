from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple, Union


TERMINAL = -1

BLACK = 0
WHITE = 1
PLAYER_NAMES = ("black", "white")
PIECE_SYMBOLS = {BLACK: "B", WHITE: "W"}
WIN_SCORE = 6

Coord = Tuple[int, int]
Direction = Tuple[int, int]
Action = Tuple[str, Tuple[Coord, ...], Direction]


DIRECTIONS: Tuple[Tuple[str, Direction], ...] = (
    ("E", (1, 0)),
    ("NE", (1, -1)),
    ("NW", (0, -1)),
    ("W", (-1, 0)),
    ("SW", (-1, 1)),
    ("SE", (0, 1)),
)
DIR_BY_NAME = {name: direction for name, direction in DIRECTIONS}
NAME_BY_DIR = {direction: name for name, direction in DIRECTIONS}

AXES: Tuple[Direction, ...] = ((1, 0), (1, -1), (0, -1))
BOARD_RADIUS = 4


def _cell_sort_key(cell: Coord) -> Tuple[int, int]:
    return (cell[1], cell[0])


def _make_board_cells() -> Tuple[Coord, ...]:
    cells: List[Coord] = []
    for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
        for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
            if max(abs(q), abs(r), abs(q + r)) <= BOARD_RADIUS:
                cells.append((q, r))
    return tuple(sorted(cells, key=_cell_sort_key))


BOARD_CELLS = _make_board_cells()
BOARD_SET = set(BOARD_CELLS)


def _add(cell: Coord, direction: Direction) -> Coord:
    return (cell[0] + direction[0], cell[1] + direction[1])


def _neg(direction: Direction) -> Direction:
    return (-direction[0], -direction[1])


def _is_on_board(cell: Coord) -> bool:
    return cell in BOARD_SET


def _projection(cell: Coord, direction: Direction) -> int:
    return cell[0] * direction[0] + cell[1] * direction[1]


def _signed_label(value: int) -> str:
    if value == 0:
        return "z0"
    if value > 0:
        return "p" + str(value)
    return "n" + str(abs(value))


def _parse_signed_label(text: str) -> int:
    if text == "z0":
        return 0
    if len(text) >= 2 and text[0] in ("p", "n") and text[1:].isdigit():
        value = int(text[1:])
        return value if text[0] == "p" else -value
    raise ValueError(f"bad signed coordinate label: {text!r}")


def cell_label(cell: Coord) -> str:
    return f"q{_signed_label(cell[0])}_r{_signed_label(cell[1])}"


def parse_cell_label(text: str) -> Coord:
    if not text.startswith("q") or "_r" not in text:
        raise ValueError(f"bad cell label: {text!r}")
    q_text, r_text = text[1:].split("_r", 1)
    cell = (_parse_signed_label(q_text), _parse_signed_label(r_text))
    if not _is_on_board(cell):
        raise ValueError(f"cell is not on the board: {text!r}")
    return cell


def _canonical_cells(cells: Iterable[Coord]) -> Tuple[Coord, ...]:
    return tuple(sorted(tuple(cells), key=_cell_sort_key))


def _parallel(direction: Direction, axis: Direction) -> bool:
    return direction == axis or direction == _neg(axis)


def _group_axis(cells: Tuple[Coord, ...]) -> Optional[Direction]:
    if len(cells) == 1:
        return None
    cell_set = set(cells)
    for axis in AXES:
        for start in cells:
            expected = {_add(start, (axis[0] * i, axis[1] * i)) for i in range(len(cells))}
            if expected == cell_set:
                return axis
    return None


def _initial_black_cells() -> Tuple[Coord, ...]:
    # Figure 1 is referenced but not textually specified in the extracted rules.
    # This assumes the standard-looking 5/6/3 setup on a radius-4 hex board.
    cells: List[Coord] = []
    for cell in BOARD_CELLS:
        q, r = cell
        if r == -4:
            cells.append(cell)
        elif r == -3:
            cells.append(cell)
        elif r == -2 and q in (0, 1, 2):
            cells.append(cell)
    return tuple(cells)


INITIAL_BLACK = _initial_black_cells()
INITIAL_WHITE = tuple(sorted(((-q, -r) for q, r in INITIAL_BLACK), key=_cell_sort_key))


@dataclass
class GameState:
    board: Dict[Coord, int]
    to_move: int = BLACK
    scores: Tuple[int, int] = (0, 0)
    winner: Optional[int] = None
    move_number: int = 0
    history: Tuple[str, ...] = field(default_factory=tuple)

    def copy(self) -> "GameState":
        return GameState(
            board=dict(self.board),
            to_move=self.to_move,
            scores=tuple(self.scores),
            winner=self.winner,
            move_number=self.move_number,
            history=tuple(self.history),
        )


class Game:
    """A small deterministic implementation of the supplied Abalone rules."""

    num_players = 2

    def initial_state(self) -> GameState:
        board: Dict[Coord, int] = {}
        for cell in INITIAL_BLACK:
            board[cell] = BLACK
        for cell in INITIAL_WHITE:
            board[cell] = WHITE
        return GameState(board=board)

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.to_move

    def legal_actions(self, state: GameState) -> List[Action]:
        if self.is_terminal(state):
            return []
        actions: List[Action] = []
        player = state.to_move
        for group in self._candidate_groups(state, player):
            if len(group) == 1:
                for _, direction in DIRECTIONS:
                    target = _add(group[0], direction)
                    if _is_on_board(target) and target not in state.board:
                        actions.append(("inline", group, direction))
                continue

            axis = _group_axis(group)
            if axis is None:
                continue
            for _, direction in DIRECTIONS:
                if _parallel(direction, axis):
                    kind = self._legal_inline_kind(state, group, direction)
                    if kind is not None:
                        actions.append((kind, group, direction))
                elif self._is_legal_side_move(state, group, direction):
                    actions.append(("side", group, direction))
        return sorted(actions, key=self.action_to_name)

    def apply_action(self, state: GameState, action: Union[Action, str]) -> GameState:
        normalized = self._normalize_action(action)
        legal = {self._normalize_action(item): item for item in self.legal_actions(state)}
        if normalized not in legal:
            raise ValueError(f"illegal action: {self.action_to_name(normalized)}")

        kind, group, direction = normalized
        player = state.to_move
        opponent = 1 - player
        next_board = dict(state.board)
        next_scores = list(state.scores)

        for cell in group:
            del next_board[cell]

        if kind == "side":
            for cell in group:
                next_board[_add(cell, direction)] = player
        else:
            ordered = sorted(group, key=lambda cell: _projection(cell, direction))
            front = ordered[-1]
            target = _add(front, direction)
            opponent_cells: List[Coord] = []
            while _is_on_board(target) and state.board.get(target) == opponent:
                opponent_cells.append(target)
                target = _add(target, direction)

            for cell in opponent_cells:
                del next_board[cell]
            for cell in reversed(opponent_cells):
                shifted = _add(cell, direction)
                if _is_on_board(shifted):
                    next_board[shifted] = opponent
                else:
                    next_scores[player] += 1
            for cell in ordered:
                next_board[_add(cell, direction)] = player

        winner = player if next_scores[player] >= WIN_SCORE else None
        action_name = self.action_to_name(normalized)
        return GameState(
            board=next_board,
            to_move=opponent if winner is None else player,
            scores=(next_scores[0], next_scores[1]),
            winner=winner,
            move_number=state.move_number + 1,
            history=state.history + (action_name,),
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or any(score >= WIN_SCORE for score in state.scores)

    def returns(self, state: GameState) -> List[float]:
        winner = state.winner
        if winner is None:
            if state.scores[BLACK] >= WIN_SCORE:
                winner = BLACK
            elif state.scores[WHITE] >= WIN_SCORE:
                winner = WHITE
        if winner is None:
            return [0.0, 0.0]
        return [1.0 if player == winner else -1.0 for player in (BLACK, WHITE)]

    def render(self, state: GameState) -> str:
        if self.is_terminal(state):
            if state.winner is None:
                winner_text = "unknown"
            else:
                winner_text = PLAYER_NAMES[state.winner]
            turn = f"terminal winner={winner_text}"
        else:
            turn = PLAYER_NAMES[state.to_move]
        lines = [
            f"to_move:{turn}",
            f"score:black={state.scores[BLACK]},white={state.scores[WHITE]}",
            f"move_number:{state.move_number}",
            "board:",
        ]
        for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
            row_cells = [cell for cell in BOARD_CELLS if cell[1] == r]
            row = " ".join(PIECE_SYMBOLS.get(state.board.get(cell), ".") for cell in row_cells)
            lines.append(f"r{_signed_label(r)}:{' ' * abs(r)}{row}")
        return "\n".join(lines)

    def action_to_name(self, action: Union[Action, str]) -> str:
        if isinstance(action, str):
            action = self.name_to_action(action)
        kind, cells, direction = self._normalize_action(action)
        if kind not in ("inline", "side", "sumito"):
            raise ValueError(f"bad action kind: {kind!r}")
        if direction not in NAME_BY_DIR:
            raise ValueError(f"bad direction: {direction!r}")
        cell_text = "+".join(cell_label(cell) for cell in cells)
        return f"move:{kind}:{cell_text}->{NAME_BY_DIR[direction]}"

    def name_to_action(self, name: str) -> Action:
        if not name.startswith("move:"):
            raise ValueError(f"bad action name: {name!r}")
        left, direction_name = name[5:].split("->", 1)
        kind, cells_text = left.split(":", 1)
        if kind not in ("inline", "side", "sumito"):
            raise ValueError(f"bad action kind: {kind!r}")
        if direction_name not in DIR_BY_NAME:
            raise ValueError(f"bad direction name: {direction_name!r}")
        cells = tuple(parse_cell_label(part) for part in cells_text.split("+") if part)
        if not cells:
            raise ValueError("action must include at least one cell")
        return self._normalize_action((kind, cells, DIR_BY_NAME[direction_name]))

    def _normalize_action(self, action: Union[Action, str]) -> Action:
        if isinstance(action, str):
            return self.name_to_action(action)
        if not isinstance(action, tuple) or len(action) != 3:
            raise ValueError(f"bad action object: {action!r}")
        kind, cells, direction = action
        if kind not in ("inline", "side", "sumito"):
            raise ValueError(f"bad action kind: {kind!r}")
        direction = tuple(direction)  # type: ignore[assignment]
        if direction not in NAME_BY_DIR:
            raise ValueError(f"bad direction: {direction!r}")
        canonical_cells = _canonical_cells(tuple(tuple(cell) for cell in cells))
        if not (1 <= len(canonical_cells) <= 3):
            raise ValueError("an action must move one, two, or three balls")
        if len(set(canonical_cells)) != len(canonical_cells):
            raise ValueError("an action cannot repeat a cell")
        for cell in canonical_cells:
            if not _is_on_board(cell):
                raise ValueError(f"cell is not on the board: {cell!r}")
        return (kind, canonical_cells, direction)  # type: ignore[return-value]

    def _candidate_groups(self, state: GameState, player: int) -> List[Tuple[Coord, ...]]:
        groups = {(cell,) for cell, owner in state.board.items() if owner == player}
        own_cells = {cell for cell, owner in state.board.items() if owner == player}
        for length in (2, 3):
            for start in own_cells:
                for axis in AXES:
                    group = tuple(_add(start, (axis[0] * i, axis[1] * i)) for i in range(length))
                    if all(cell in own_cells for cell in group):
                        groups.add(_canonical_cells(group))
        return sorted(groups, key=lambda group: (len(group), tuple(_cell_sort_key(cell) for cell in group)))

    def _is_legal_side_move(self, state: GameState, group: Tuple[Coord, ...], direction: Direction) -> bool:
        for cell in group:
            target = _add(cell, direction)
            if not _is_on_board(target) or target in state.board:
                return False
        return True

    def _legal_inline_kind(
        self, state: GameState, group: Tuple[Coord, ...], direction: Direction
    ) -> Optional[str]:
        player = state.to_move
        opponent = 1 - player
        ordered = sorted(group, key=lambda cell: _projection(cell, direction))
        front = ordered[-1]
        target = _add(front, direction)
        if not _is_on_board(target):
            return None
        occupant = state.board.get(target)
        if occupant is None:
            return "inline"
        if occupant == player:
            return None

        opponent_count = 0
        scan = target
        while _is_on_board(scan) and state.board.get(scan) == opponent:
            opponent_count += 1
            scan = _add(scan, direction)
        if opponent_count == 0 or opponent_count >= len(group):
            return None
        if opponent_count > 2:
            return None
        if not _is_on_board(scan):
            return "sumito"
        if scan not in state.board:
            return "sumito"
        return None


__all__ = [
    "TERMINAL",
    "BLACK",
    "WHITE",
    "GameState",
    "Game",
    "cell_label",
    "parse_cell_label",
]
