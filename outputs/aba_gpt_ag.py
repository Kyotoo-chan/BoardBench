"""Self-contained Abalone implementation from the supplied German rulebook.

Documented assumptions where the rulebook text/figures are incomplete:
- The board is the hexagonal field shown in Fig. 1: nine rows with lengths
  5, 6, 7, 8, 9, 8, 7, 6, 5.
- The initial position is read from Fig. 1 as black on the top two rows plus
  the center three holes of the third row, and white mirrored at the bottom.
- The rulebook gives no coordinate labels, so this implementation labels holes
  by display row/column (R1C1 is the top-left hole).
- A two- or three-marble move selects contiguous own marbles in one straight
  line.  Longer lines may be split by selecting a contiguous window of 1-3.
- Sumito pushes may push the last opposing marble off the board, because the
  "Hinausschieben" section describes a marble leaving the field when pushed
  onto the rim.  Equal-strength Patt positions are illegal pushes because a
  push requires strictly more attacking marbles than defending marbles.
- Chess-clock play, draws, repetition, resignation, and tournament procedures
  are not specified and are not modeled.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

TERMINAL = -1

EMPTY = "."
PLAYER_PIECES = ("B", "W")  # player 0 is black; player 1 is white.
PLAYER_NAMES = ("black", "white")
WIN_PUSHED_OFF = 6

Coord = Tuple[int, int]

# Axial hex directions.  With rows rendered top-to-bottom, E/W stay in a row,
# SE/SW move down, and NE/NW move up.
DIRECTIONS: Dict[str, Coord] = {
    "E": (1, 0),
    "SE": (0, 1),
    "SW": (-1, 1),
    "W": (-1, 0),
    "NW": (0, -1),
    "NE": (1, -1),
}
DIRECTION_NAMES = ("E", "SE", "SW", "W", "NW", "NE")
OPPOSITE = {"E": "W", "W": "E", "SE": "NW", "NW": "SE", "SW": "NE", "NE": "SW"}
# One representative for each of the three straight-line axes.
AXIS_NAMES = ("E", "SE", "NE")

ROW_LENGTHS = (5, 6, 7, 8, 9, 8, 7, 6, 5)

CELLS: List[Coord] = []
CELL_TO_LABEL: Dict[Coord, str] = {}
LABEL_TO_CELL: Dict[str, Coord] = {}
ROW_CELLS: List[Tuple[Coord, ...]] = []

for row_number, r in enumerate(range(-4, 5), start=1):
    q_min = max(-4, -r - 4)
    q_max = min(4, -r + 4)
    row: List[Coord] = []
    for col_number, q in enumerate(range(q_min, q_max + 1), start=1):
        cell = (q, r)
        label = f"R{row_number}C{col_number}"
        CELLS.append(cell)
        row.append(cell)
        CELL_TO_LABEL[cell] = label
        LABEL_TO_CELL[label] = cell
    ROW_CELLS.append(tuple(row))

CELL_TO_INDEX: Dict[Coord, int] = {cell: i for i, cell in enumerate(CELLS)}
INDEX_TO_CELL: Tuple[Coord, ...] = tuple(CELLS)
CELL_COUNT = len(CELLS)


def _add(cell: Coord, direction: Coord) -> Coord:
    return (cell[0] + direction[0], cell[1] + direction[1])


def _neg(direction: Coord) -> Coord:
    return (-direction[0], -direction[1])


def _on_board(cell: Coord) -> bool:
    return cell in CELL_TO_INDEX


def _piece_at(board: Sequence[str], cell: Coord) -> str:
    return board[CELL_TO_INDEX[cell]]


def _label(cell: Coord) -> str:
    return CELL_TO_LABEL[cell]


def _labels(cells: Iterable[Coord]) -> List[str]:
    return [_label(cell) for cell in sorted(cells, key=lambda c: CELL_TO_INDEX[c])]


def _source_text(cells: Iterable[Coord]) -> str:
    return "+".join(_labels(cells))


def _cells_from_source_text(text: str) -> Tuple[Coord, ...]:
    if not text:
        raise ValueError("empty source list")
    cells = []
    for part in text.split("+"):
        if part not in LABEL_TO_CELL:
            raise ValueError(f"unknown cell label: {part}")
        cells.append(LABEL_TO_CELL[part])
    return tuple(cells)


def _front_cell(group: Sequence[Coord], direction: Coord) -> Coord:
    group_set = set(group)
    fronts = [cell for cell in group if _add(cell, direction) not in group_set]
    if len(fronts) != 1:
        raise ValueError("group is not a single contiguous line in that direction")
    return fronts[0]


def _ordered_front_to_back(group: Sequence[Coord], direction: Coord) -> List[Coord]:
    group_set = set(group)
    ordered = [_front_cell(group, direction)]
    back_step = _neg(direction)
    while True:
        nxt = _add(ordered[-1], back_step)
        if nxt not in group_set:
            return ordered
        ordered.append(nxt)


def _initial_board() -> Tuple[str, ...]:
    board = [EMPTY] * CELL_COUNT

    def set_piece(label: str, piece: str) -> None:
        board[CELL_TO_INDEX[LABEL_TO_CELL[label]]] = piece

    # Fig. 1 setup, using the implementation's row/column labels.
    for label in ("R1C1", "R1C2", "R1C3", "R1C4", "R1C5"):
        set_piece(label, "B")
    for label in ("R2C1", "R2C2", "R2C3", "R2C4", "R2C5", "R2C6"):
        set_piece(label, "B")
    for label in ("R3C3", "R3C4", "R3C5"):
        set_piece(label, "B")

    for label in ("R9C1", "R9C2", "R9C3", "R9C4", "R9C5"):
        set_piece(label, "W")
    for label in ("R8C1", "R8C2", "R8C3", "R8C4", "R8C5", "R8C6"):
        set_piece(label, "W")
    for label in ("R7C3", "R7C4", "R7C5"):
        set_piece(label, "W")

    return tuple(board)


INITIAL_BOARD = _initial_board()


@dataclass(frozen=True)
class GameState:
    board: Tuple[str, ...]
    to_move: int = 0
    pushed_off: Tuple[int, int] = (0, 0)  # opponent marbles pushed off by each player
    winner: Optional[int] = None
    history: Tuple[str, ...] = ()


class Game:
    """Minimal deterministic two-player Abalone API."""

    num_players = 2
    player_names = PLAYER_NAMES

    def initial_state(self) -> GameState:
        return GameState(board=INITIAL_BOARD, to_move=0, pushed_off=(0, 0), winner=None, history=())

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.to_move

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        return sorted(_legal_actions(state))

    def apply_action(self, state: GameState, action: str) -> GameState:
        action = self.action_to_name(action)
        legal = set(self.legal_actions(state))
        if action not in legal:
            raise ValueError(f"illegal action for this state: {action}")

        kind, mode, sources, direction_name = _parse_action(action)
        direction = DIRECTIONS[direction_name]
        board = list(state.board)
        player = state.to_move
        pushed_off = list(state.pushed_off)

        if kind == "push":
            if _apply_push(board, sources, direction, player):
                pushed_off[player] += 1
        elif mode in ("single", "line"):
            _apply_line_move(board, sources, direction)
        elif mode == "side":
            _apply_side_move(board, sources, direction)
        else:  # The parser should prevent this.
            raise ValueError(f"unknown action mode: {mode}")

        winner: Optional[int] = None
        for p, count in enumerate(pushed_off):
            if count >= WIN_PUSHED_OFF:
                winner = p
                break

        next_player = 1 - player
        return GameState(
            board=tuple(board),
            to_move=next_player,
            pushed_off=(pushed_off[0], pushed_off[1]),
            winner=winner,
            history=state.history + (action,),
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or any(count >= WIN_PUSHED_OFF for count in state.pushed_off)

    def returns(self, state: GameState) -> List[float]:
        winner = state.winner
        if winner is None:
            for p, count in enumerate(state.pushed_off):
                if count >= WIN_PUSHED_OFF:
                    winner = p
                    break
        if winner is None:
            return [0.0, 0.0]
        return [1.0 if p == winner else -1.0 for p in range(self.num_players)]

    def render(self, state: GameState) -> str:
        turn = "terminal" if self.is_terminal(state) else PLAYER_PIECES[state.to_move]
        lines = [
            f"turn:{turn} pushed_off:B={state.pushed_off[0]} W={state.pushed_off[1]}",
        ]
        for row_number, row in enumerate(ROW_CELLS, start=1):
            contents = " ".join(_piece_at(state.board, cell) for cell in row)
            lines.append(f"R{row_number}: {contents}")
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are represented by their canonical string names")
        # Validate syntax, but not state-specific legality.
        _parse_action(action)
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names must be strings")
        _parse_action(name)
        return name


def _parse_action(action: str) -> Tuple[str, str, Tuple[Coord, ...], str]:
    parts = action.split(":")
    if len(parts) == 4 and parts[0] == "move":
        mode = parts[1]
        if mode not in ("single", "line", "side"):
            raise ValueError(f"unknown move mode: {mode}")
        sources = _cells_from_source_text(parts[2])
        direction_name = parts[3]
        kind = "move"
    elif len(parts) == 3 and parts[0] == "push":
        mode = "push"
        sources = _cells_from_source_text(parts[1])
        direction_name = parts[2]
        kind = "push"
    else:
        raise ValueError(f"not a canonical action name: {action}")

    if direction_name not in DIRECTIONS:
        raise ValueError(f"unknown direction: {direction_name}")
    if len(set(sources)) != len(sources):
        raise ValueError("duplicate source in action")
    if mode == "single" and len(sources) != 1:
        raise ValueError("single moves need exactly one source")
    if mode in ("line", "side", "push") and len(sources) not in (2, 3):
        raise ValueError("line, side, and push moves need two or three sources")
    return kind, mode, sources, direction_name


def _legal_actions(state: GameState) -> List[str]:
    board = state.board
    player = state.to_move
    own = PLAYER_PIECES[player]
    opp = PLAYER_PIECES[1 - player]
    actions = set()

    own_cells = [cell for cell in CELLS if _piece_at(board, cell) == own]

    # One-marble moves: the adjacent target hole must be on the board and empty.
    for cell in own_cells:
        for direction_name in DIRECTION_NAMES:
            direction = DIRECTIONS[direction_name]
            dest = _add(cell, direction)
            if _on_board(dest) and _piece_at(board, dest) == EMPTY:
                actions.add(f"move:single:{_label(cell)}:{direction_name}")

    # Two- and three-marble straight contiguous groups.
    for group, axis_name in _candidate_groups(board, own):
        source = _source_text(group)
        for direction_name in DIRECTION_NAMES:
            direction = DIRECTIONS[direction_name]
            if direction_name in (axis_name, OPPOSITE[axis_name]):
                inline = _inline_move_kind(board, group, direction, own, opp)
                if inline == "line":
                    actions.add(f"move:line:{source}:{direction_name}")
                elif inline == "push":
                    actions.add(f"push:{source}:{direction_name}")
            else:
                if _side_move_is_legal(board, group, direction):
                    actions.add(f"move:side:{source}:{direction_name}")

    return list(actions)


def _candidate_groups(board: Sequence[str], own_piece: str) -> Iterable[Tuple[Tuple[Coord, ...], str]]:
    for axis_name in AXIS_NAMES:
        step = DIRECTIONS[axis_name]
        for start in CELLS:
            for size in (2, 3):
                group = tuple((start[0] + i * step[0], start[1] + i * step[1]) for i in range(size))
                if all(_on_board(cell) and _piece_at(board, cell) == own_piece for cell in group):
                    yield group, axis_name


def _inline_move_kind(
    board: Sequence[str], group: Sequence[Coord], direction: Coord, own_piece: str, opp_piece: str
) -> Optional[str]:
    front = _front_cell(group, direction)
    first = _add(front, direction)
    if not _on_board(first):
        return None

    first_piece = _piece_at(board, first)
    if first_piece == EMPTY:
        return "line"
    if first_piece != opp_piece:
        return None

    defenders = []
    cur = first
    while _on_board(cur) and _piece_at(board, cur) == opp_piece:
        defenders.append(cur)
        cur = _add(cur, direction)

    # Sumito: only 2-vs-1, 3-vs-1, and 3-vs-2. Equal Patt cannot push.
    if len(defenders) not in (1, 2):
        return None
    if len(group) <= len(defenders):
        return None
    if not _on_board(cur) or _piece_at(board, cur) == EMPTY:
        return "push"
    return None


def _side_move_is_legal(board: Sequence[str], group: Sequence[Coord], direction: Coord) -> bool:
    for cell in group:
        dest = _add(cell, direction)
        if not _on_board(dest) or _piece_at(board, dest) != EMPTY:
            return False
    return True


def _apply_line_move(board: List[str], group: Sequence[Coord], direction: Coord) -> None:
    for cell in _ordered_front_to_back(group, direction):
        dest = _add(cell, direction)
        board[CELL_TO_INDEX[dest]] = board[CELL_TO_INDEX[cell]]
        board[CELL_TO_INDEX[cell]] = EMPTY


def _apply_side_move(board: List[str], group: Sequence[Coord], direction: Coord) -> None:
    piece = board[CELL_TO_INDEX[group[0]]]
    for cell in group:
        board[CELL_TO_INDEX[cell]] = EMPTY
    for cell in group:
        dest = _add(cell, direction)
        board[CELL_TO_INDEX[dest]] = piece


def _apply_push(board: List[str], group: Sequence[Coord], direction: Coord, player: int) -> bool:
    opp_piece = PLAYER_PIECES[1 - player]
    front = _front_cell(group, direction)
    cur = _add(front, direction)
    defenders: List[Coord] = []
    while _on_board(cur) and board[CELL_TO_INDEX[cur]] == opp_piece:
        defenders.append(cur)
        cur = _add(cur, direction)

    pushed_one_off = not _on_board(cur)
    if pushed_one_off:
        # The farthest defender leaves the board; the rest slide forward.
        farthest = defenders[-1]
        board[CELL_TO_INDEX[farthest]] = EMPTY
        defenders_to_move = defenders[:-1]
    else:
        defenders_to_move = defenders

    for defender in reversed(defenders_to_move):
        dest = _add(defender, direction)
        board[CELL_TO_INDEX[dest]] = opp_piece
        board[CELL_TO_INDEX[defender]] = EMPTY

    _apply_line_move(board, group, direction)
    return pushed_one_off
