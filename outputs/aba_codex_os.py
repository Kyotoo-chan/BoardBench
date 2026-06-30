from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

BLACK = 0
WHITE = 1
TERMINAL = -1

PLAYER_NAMES = ("black", "white")
TARGET_OFF = 6

Coord = Tuple[int, int]
Action = Tuple[str, Tuple[Coord, ...], str]

DIRECTIONS = (
    ("E", (1, 0)),
    ("NE", (1, -1)),
    ("NW", (0, -1)),
    ("W", (-1, 0)),
    ("SW", (-1, 1)),
    ("SE", (0, 1)),
)
DIR_DELTA = dict(DIRECTIONS)
DIR_NAMES = tuple(name for name, _ in DIRECTIONS)
AXIS_NAMES = ("E", "NE", "NW")
OPPOSITE = {"E": "W", "NE": "SW", "NW": "SE", "W": "E", "SW": "NE", "SE": "NW"}


@dataclass(frozen=True)
class GameState:
    # board stores only occupied holes as ((q, r), player).
    board: Tuple[Tuple[Coord, int], ...]
    current: int
    off: Tuple[int, int] = (0, 0)  # marbles of each color pushed out
    turn: int = 0
    winner: Optional[int] = None
    history: Tuple[str, ...] = ()


def _add(a: Coord, b: Coord) -> Coord:
    return (a[0] + b[0], a[1] + b[1])


def _coord_sort_key(coord: Coord) -> Tuple[int, int]:
    return (coord[1], coord[0])


def _signed(value: int) -> str:
    if value < 0:
        return "n" + str(abs(value))
    if value > 0:
        return "p" + str(value)
    return "z0"


def _coord_label(coord: Coord) -> str:
    return "q%s_r%s" % (_signed(coord[0]), _signed(coord[1]))


def _parse_signed(text: str) -> int:
    if len(text) < 2 or not text[1:].isdigit():
        raise ValueError("bad signed coordinate part: %r" % text)
    sign = text[0]
    value = int(text[1:])
    if sign == "p":
        return value
    if sign == "n":
        return -value
    if sign == "z" and value == 0:
        return 0
    raise ValueError("bad signed coordinate part: %r" % text)


def _parse_coord_label(text: str) -> Coord:
    if not text.startswith("q") or "_r" not in text:
        raise ValueError("bad coordinate label: %r" % text)
    q_text, r_text = text[1:].split("_r", 1)
    return (_parse_signed(q_text), _parse_signed(r_text))


def _make_hex_board(radius: int) -> Tuple[Coord, ...]:
    cells: List[Coord] = []
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= radius:
                cells.append((q, r))
    return tuple(sorted(cells, key=_coord_sort_key))


def _default_start(cells: Iterable[Coord], count: int) -> Tuple[Tuple[Coord, ...], Tuple[Coord, ...]]:
    # Placeholder only: the real start diagram was referenced but not provided.
    ordered = sorted(cells, key=_coord_sort_key)
    white = tuple(ordered[:count])
    black = tuple(sorted(((-q, -r) for q, r in white), key=_coord_sort_key))
    return black, white


def _pack_board(board: Dict[Coord, int]) -> Tuple[Tuple[Coord, int], ...]:
    return tuple(sorted(board.items(), key=lambda item: _coord_sort_key(item[0])))


class Game:
    num_players = 2

    def __init__(
        self,
        radius: int = 3,
        black_start: Optional[Iterable[Coord]] = None,
        white_start: Optional[Iterable[Coord]] = None,
        target_off: int = TARGET_OFF,
    ):
        self.radius = radius
        self.cells = frozenset(_make_hex_board(radius))
        self.target_off = target_off

        if black_start is None and white_start is None:
            black_start, white_start = _default_start(self.cells, self.target_off)
        elif black_start is None or white_start is None:
            raise ValueError("provide both black_start and white_start, or neither")

        self.black_start = tuple(self._normalize_coord(c) for c in black_start)
        self.white_start = tuple(self._normalize_coord(c) for c in white_start)
        self._validate_start()

    def _normalize_coord(self, coord: Coord) -> Coord:
        q, r = coord
        parsed = (int(q), int(r))
        if parsed not in self.cells:
            raise ValueError("coordinate outside board: %r" % (coord,))
        return parsed

    def _validate_start(self) -> None:
        black = set(self.black_start)
        white = set(self.white_start)
        if len(black) != len(self.black_start) or len(white) != len(self.white_start):
            raise ValueError("duplicate start coordinate")
        if black & white:
            raise ValueError("black and white starts overlap")
        if len(black) < self.target_off or len(white) < self.target_off:
            raise ValueError("each player needs at least target_off marbles")

    def initial_state(self) -> GameState:
        board: Dict[Coord, int] = {}
        for coord in self.black_start:
            board[coord] = BLACK
        for coord in self.white_start:
            board[coord] = WHITE
        return GameState(board=_pack_board(board), current=BLACK)

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.current

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or state.off[BLACK] >= self.target_off or state.off[WHITE] >= self.target_off

    def returns(self, state: GameState) -> List[float]:
        winner = state.winner if state.winner is not None else self._winner_from_off(state.off)
        if winner == BLACK:
            return [1.0, -1.0]
        if winner == WHITE:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def legal_actions(self, state: GameState) -> List[Action]:
        if self.is_terminal(state):
            return []

        board = self._board_dict(state)
        player = state.current
        actions: Set[Action] = set()

        for group in self._groups_for_player(board, player):
            if len(group) == 1:
                source = group[0]
                for direction in DIR_NAMES:
                    dest = _add(source, DIR_DELTA[direction])
                    if dest in self.cells and board.get(dest) is None:
                        actions.add(("move", group, direction))
                continue

            axis, _ = self._group_axis_and_order(group)
            for direction in DIR_NAMES:
                if self._is_parallel(direction, axis):
                    kind = self._legal_inline_kind(board, player, group, direction)
                    if kind is not None:
                        actions.add((kind, group, direction))
                elif self._legal_side_move(board, group, direction):
                    actions.add(("side", group, direction))

        return sorted(actions, key=self.action_to_name)

    def apply_action(self, state: GameState, action: Action) -> GameState:
        legal = set(self.legal_actions(state))
        if action not in legal:
            try:
                name = self.action_to_name(action)
            except Exception:
                name = repr(action)
            raise ValueError("illegal action: %s" % name)

        kind, group, direction = action
        delta = DIR_DELTA[direction]
        board = self._board_dict(state)
        player = state.current
        off = [state.off[BLACK], state.off[WHITE]]

        if kind in ("move", "line", "side"):
            for coord in group:
                del board[coord]
            for coord in group:
                board[_add(coord, delta)] = player

        elif kind == "sumito":
            front = self._front_cell(group, direction)
            first_opp = _add(front, delta)
            opp_cells, _ = self._opponent_run(board, first_opp, direction, player)
            opponent = 1 - player

            for coord in tuple(group) + opp_cells:
                del board[coord]

            for coord in opp_cells:
                dest = _add(coord, delta)
                if dest in self.cells:
                    board[dest] = opponent
                else:
                    off[opponent] += 1

            for coord in group:
                board[_add(coord, delta)] = player

        off_tuple = (off[BLACK], off[WHITE])
        winner = self._winner_from_off(off_tuple)
        terminal = off_tuple[BLACK] >= self.target_off or off_tuple[WHITE] >= self.target_off
        next_player = TERMINAL if terminal else 1 - player
        history = state.history + (self.action_to_name(action),)

        return GameState(
            board=_pack_board(board),
            current=next_player,
            off=off_tuple,
            turn=state.turn + 1,
            winner=winner,
            history=history,
        )

    def render(self, state: GameState) -> str:
        board = self._board_dict(state)
        black = []
        white = []
        for coord, player in sorted(board.items(), key=lambda item: _coord_sort_key(item[0])):
            if player == BLACK:
                black.append(_coord_label(coord))
            else:
                white.append(_coord_label(coord))

        current = "terminal" if self.is_terminal(state) else PLAYER_NAMES[state.current]
        winner = state.winner if state.winner is not None else self._winner_from_off(state.off)
        winner_text = "-" if winner is None else PLAYER_NAMES[winner]
        last = state.history[-1] if state.history else "-"

        return "\n".join(
            [
                "turn=%d current=%s winner=%s" % (state.turn, current, winner_text),
                "off_black=%d off_white=%d" % (state.off[BLACK], state.off[WHITE]),
                "black=%s" % (",".join(black) if black else "-"),
                "white=%s" % (",".join(white) if white else "-"),
                "last=%s" % last,
            ]
        )

    def action_to_name(self, action: Action) -> str:
        kind, group, direction = action
        if kind not in ("move", "line", "side", "sumito"):
            raise ValueError("bad action kind: %r" % (kind,))
        if direction not in DIR_DELTA:
            raise ValueError("bad direction: %r" % (direction,))
        return "%s:%s->%s" % (kind, ",".join(_coord_label(c) for c in group), direction)

    def name_to_action(self, name: str) -> Action:
        kind, rest = name.split(":", 1)
        cells_text, direction = rest.split("->", 1)
        if kind not in ("move", "line", "side", "sumito"):
            raise ValueError("bad action kind: %r" % (kind,))
        if direction not in DIR_DELTA:
            raise ValueError("bad direction: %r" % (direction,))
        group = tuple(_parse_coord_label(part) for part in cells_text.split(","))
        if not group:
            raise ValueError("action must name at least one marble")
        return (kind, group, direction)

    def _board_dict(self, state: GameState) -> Dict[Coord, int]:
        return dict(state.board)

    def _winner_from_off(self, off: Tuple[int, int]) -> Optional[int]:
        black_off, white_off = off
        if black_off >= self.target_off and white_off >= self.target_off:
            return None
        if white_off >= self.target_off:
            return BLACK
        if black_off >= self.target_off:
            return WHITE
        return None

    def _groups_for_player(self, board: Dict[Coord, int], player: int) -> List[Tuple[Coord, ...]]:
        groups: Set[Tuple[Coord, ...]] = set()

        for coord, occupant in board.items():
            if occupant == player:
                groups.add((coord,))

        for axis in AXIS_NAMES:
            delta = DIR_DELTA[axis]
            for start in sorted(self.cells, key=_coord_sort_key):
                seq: List[Coord] = []
                for step in range(3):
                    coord = (start[0] + delta[0] * step, start[1] + delta[1] * step)
                    if coord in self.cells and board.get(coord) == player:
                        seq.append(coord)
                        if len(seq) >= 2:
                            groups.add(tuple(seq))
                    else:
                        break

        return sorted(groups, key=lambda g: (len(g), tuple(_coord_sort_key(c) for c in g)))

    def _group_axis_and_order(self, group: Tuple[Coord, ...]) -> Tuple[str, Tuple[Coord, ...]]:
        if len(group) < 2:
            raise ValueError("single marble group has no axis")
        wanted = set(group)
        for axis in AXIS_NAMES:
            delta = DIR_DELTA[axis]
            for start in wanted:
                seq = tuple((start[0] + delta[0] * i, start[1] + delta[1] * i) for i in range(len(group)))
                if set(seq) == wanted:
                    return axis, seq
        raise ValueError("group is not a contiguous straight line: %r" % (group,))

    def _is_parallel(self, direction: str, axis: str) -> bool:
        return direction == axis or direction == OPPOSITE[axis]

    def _front_cell(self, group: Tuple[Coord, ...], direction: str) -> Coord:
        if len(group) == 1:
            return group[0]
        axis, ordered = self._group_axis_and_order(group)
        if direction == axis:
            return ordered[-1]
        if direction == OPPOSITE[axis]:
            return ordered[0]
        raise ValueError("direction is not inline with group")

    def _legal_side_move(self, board: Dict[Coord, int], group: Tuple[Coord, ...], direction: str) -> bool:
        delta = DIR_DELTA[direction]
        for coord in group:
            dest = _add(coord, delta)
            if dest not in self.cells or board.get(dest) is not None:
                return False
        return True

    def _legal_inline_kind(
        self,
        board: Dict[Coord, int],
        player: int,
        group: Tuple[Coord, ...],
        direction: str,
    ) -> Optional[str]:
        delta = DIR_DELTA[direction]
        front = self._front_cell(group, direction)
        dest = _add(front, delta)

        if dest not in self.cells:
            return None

        occupant = board.get(dest)
        if occupant is None:
            return "line"
        if occupant == player:
            return None

        opp_cells, beyond = self._opponent_run(board, dest, direction, player)
        if len(opp_cells) >= len(group):
            return None
        if beyond in self.cells and board.get(beyond) is not None:
            return None

        # If beyond is outside the board, the front opponent marble is pushed out.
        return "sumito"

    def _opponent_run(
        self,
        board: Dict[Coord, int],
        start: Coord,
        direction: str,
        player: int,
    ) -> Tuple[Tuple[Coord, ...], Coord]:
        opponent = 1 - player
        delta = DIR_DELTA[direction]
        cells: List[Coord] = []
        coord = start
        while coord in self.cells and board.get(coord) == opponent:
            cells.append(coord)
            coord = _add(coord, delta)
        return tuple(cells), coord
