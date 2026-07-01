"""Self-contained Abalone-like implementation from the provided German rules.

Known gap: Figure 1/start setup and exact board labels are missing.  The default
board/setup below is an explicit placeholder, not a claim of official layout.
"""

from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Optional, Set, Tuple

TERMINAL = -1
BLACK = 0
WHITE = 1
PLAYER_NAMES = ("B", "W")

Cell = Tuple[int, int]
Direction = Tuple[int, int]

DIRECTIONS: Tuple[Tuple[str, Direction], ...] = (
    ("E", (1, 0)),
    ("NE", (1, -1)),
    ("NW", (0, -1)),
    ("W", (-1, 0)),
    ("SW", (-1, 1)),
    ("SE", (0, 1)),
)
DIRECTION_BY_NAME = dict(DIRECTIONS)
AXES: Tuple[Direction, ...] = (
    DIRECTION_BY_NAME["E"],
    DIRECTION_BY_NAME["NE"],
    DIRECTION_BY_NAME["NW"],
)


def _coerce_cell(value) -> Cell:
    q, r = value
    if not isinstance(q, int) or not isinstance(r, int):
        raise ValueError("cell coordinates must be integers")
    return (q, r)


def _add(cell: Cell, direction: Direction, steps: int = 1) -> Cell:
    return (cell[0] + direction[0] * steps, cell[1] + direction[1] * steps)


def _neg(direction: Direction) -> Direction:
    return (-direction[0], -direction[1])


def _hex_cells(radius: int) -> FrozenSet[Cell]:
    return frozenset(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(-q - r)) <= radius
    )


def _encode_int(n: int) -> str:
    if n == 0:
        return "Z"
    return ("P" + str(n)) if n > 0 else ("N" + str(-n))


def _decode_int(text: str) -> int:
    if text == "Z":
        return 0
    if len(text) < 2 or text[0] not in ("P", "N") or not text[1:].isdigit():
        raise ValueError("bad signed coordinate")
    value = int(text[1:])
    return value if text[0] == "P" else -value


def _cell_label(cell: Cell) -> str:
    q, r = cell
    return "q%s_r%s" % (_encode_int(q), _encode_int(r))


def _parse_cell_label(label: str) -> Cell:
    parts = label.split("_")
    if len(parts) != 2 or not parts[0].startswith("q") or not parts[1].startswith("r"):
        raise ValueError("bad cell label")
    return (_decode_int(parts[0][1:]), _decode_int(parts[1][1:]))


def _canonical_cells(cells: Iterable[Cell]) -> Tuple[Cell, ...]:
    return tuple(sorted((_coerce_cell(c) for c in cells), key=_cell_label))


def _format_action(cells: Iterable[Cell], dir_name: str) -> str:
    if dir_name not in DIRECTION_BY_NAME:
        raise ValueError("bad direction")
    canonical = _canonical_cells(cells)
    if not 1 <= len(canonical) <= 3:
        raise ValueError("a move must name one, two, or three balls")
    if len(set(canonical)) != len(canonical):
        raise ValueError("duplicate cell in action")
    return "move:%s:%s" % (",".join(_cell_label(c) for c in canonical), dir_name)


def _parse_action_name(name: str) -> Tuple[Tuple[Cell, ...], str]:
    if not isinstance(name, str):
        raise TypeError("actions are canonical strings")
    if not name.startswith("move:"):
        raise ValueError("bad action prefix")
    body = name[len("move:") :]
    if ":" not in body:
        raise ValueError("bad action")
    cell_text, dir_name = body.rsplit(":", 1)
    if dir_name not in DIRECTION_BY_NAME:
        raise ValueError("bad direction")
    labels = cell_text.split(",")
    cells = tuple(_parse_cell_label(x) for x in labels if x)
    if len(cells) != len(labels):
        raise ValueError("empty cell label")
    if not 1 <= len(cells) <= 3:
        raise ValueError("a move must name one, two, or three balls")
    if len(set(cells)) != len(cells):
        raise ValueError("duplicate cell in action")
    return _canonical_cells(cells), dir_name


@dataclass(frozen=True)
class GameState:
    black: FrozenSet[Cell]
    white: FrozenSet[Cell]
    pushed_off_by: Tuple[int, int] = (0, 0)
    current: int = BLACK
    turn: int = 0
    winner: Optional[int] = None

    def __post_init__(self) -> None:
        black = frozenset(_coerce_cell(c) for c in self.black)
        white = frozenset(_coerce_cell(c) for c in self.white)
        if black & white:
            raise ValueError("a cell cannot contain both colors")
        scores = tuple(self.pushed_off_by)
        if len(scores) != 2 or any((not isinstance(x, int) or x < 0) for x in scores):
            raise ValueError("pushed_off_by must contain two non-negative integers")
        if self.current not in (BLACK, WHITE, TERMINAL):
            raise ValueError("bad current player")
        if self.winner not in (None, BLACK, WHITE):
            raise ValueError("bad winner")
        if not isinstance(self.turn, int) or self.turn < 0:
            raise ValueError("turn must be a non-negative integer")
        object.__setattr__(self, "black", black)
        object.__setattr__(self, "white", white)
        object.__setattr__(self, "pushed_off_by", scores)


class Game:
    """Two-player deterministic public-information game."""

    num_players = 2

    def __init__(
        self,
        radius: int = 3,
        black_positions: Optional[Iterable[Cell]] = None,
        white_positions: Optional[Iterable[Cell]] = None,
        target_pushed: int = 6,
    ):
        # Radius 3 is the smallest regular hex with a 7-cell line, allowing the
        # rulebook's described 4-to-3 Patt example. Exact board figure is absent.
        if not isinstance(radius, int) or radius < 3:
            raise ValueError("radius must be an integer at least 3")
        if not isinstance(target_pushed, int) or target_pushed <= 0:
            raise ValueError("target_pushed must be positive")
        self.radius = radius
        self.cells = _hex_cells(radius)
        self.target_pushed = target_pushed

        if black_positions is None:
            black = frozenset(c for c in self.cells if c[1] <= -radius + 1)
        else:
            black = self._coerce_positions(black_positions)

        if white_positions is None:
            white = frozenset(c for c in self.cells if c[1] >= radius - 1)
        else:
            white = self._coerce_positions(white_positions)

        outside = (black | white) - self.cells
        if outside:
            raise ValueError("initial position outside board: " + _cell_label(sorted(outside)[0]))
        if black & white:
            raise ValueError("initial black/white positions overlap")
        if len(black) < target_pushed or len(white) < target_pushed:
            raise ValueError("each side needs at least target_pushed balls")

        self.initial_black = black
        self.initial_white = white

    def _coerce_positions(self, positions: Iterable[Cell]) -> FrozenSet[Cell]:
        return frozenset(_coerce_cell(c) for c in positions)

    def initial_state(self) -> GameState:
        return GameState(
            black=self.initial_black,
            white=self.initial_white,
            pushed_off_by=(0, 0),
            current=BLACK,  # Black always starts.
            turn=0,
            winner=None,
        )

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.current

    def legal_actions(self, state: GameState) -> List[str]:
        if self._score_terminal(state):
            return []
        return self._legal_action_names(state)

    def apply_action(self, state: GameState, action: str) -> GameState:
        canonical = self.action_to_name(action)
        if canonical != action:
            raise ValueError("action is not canonical; use %r" % canonical)
        if canonical not in set(self.legal_actions(state)):
            raise ValueError("illegal action: %s" % canonical)

        cells, dir_name = _parse_action_name(canonical)
        delta = DIRECTION_BY_NAME[dir_name]
        player = state.current
        opponent = WHITE if player == BLACK else BLACK
        group = frozenset(cells)

        own_cells = set(self._player_cells(state, player))
        opponent_cells = set(self._player_cells(state, opponent))

        push_line: List[Cell] = []
        if len(group) > 1:
            axis = self._group_axis(group)
            if axis is not None and (delta == axis or delta == _neg(axis)):
                front = self._front_cell(group, delta)
                dest = _add(front, delta)
                if dest in opponent_cells:
                    push_line, _ = self._opponent_line(opponent_cells, dest, delta)

        for c in group:
            own_cells.remove(c)
        for c in group:
            own_cells.add(_add(c, delta))

        scores = list(state.pushed_off_by)
        if push_line:
            for c in push_line:
                opponent_cells.remove(c)
            for c in push_line:
                moved = _add(c, delta)
                if moved in self.cells:
                    opponent_cells.add(moved)
                else:
                    scores[player] += 1

        if player == BLACK:
            black, white = frozenset(own_cells), frozenset(opponent_cells)
        else:
            white, black = frozenset(own_cells), frozenset(opponent_cells)

        winner = player if scores[player] >= self.target_pushed else None
        return GameState(
            black=black,
            white=white,
            pushed_off_by=(scores[0], scores[1]),
            current=opponent,
            turn=state.turn + 1,
            winner=winner,
        )

    def is_terminal(self, state: GameState) -> bool:
        if self._score_terminal(state):
            return True
        # Rulebook does not define stalemate/no-move; assumption: draw terminal.
        return len(self._legal_action_names(state)) == 0

    def returns(self, state: GameState) -> Tuple[float, float]:
        winner = self._winner(state)
        if winner == BLACK:
            return (1.0, -1.0)
        if winner == WHITE:
            return (-1.0, 1.0)
        return (0.0, 0.0)

    def render(self, state: GameState) -> str:
        cp = self.current_player(state)
        current = "T" if cp == TERMINAL else PLAYER_NAMES[cp]
        winner = self._winner(state)
        winner_text = "-" if winner is None else PLAYER_NAMES[winner]
        lines = [
            "turn:%d current:%s pushed_off:B=%d,W=%d winner:%s"
            % (state.turn, current, state.pushed_off_by[0], state.pushed_off_by[1], winner_text)
        ]
        for r in range(-self.radius, self.radius + 1):
            row = sorted((c for c in self.cells if c[1] == r), key=lambda c: c[0])
            tokens = []
            for q, _ in row:
                cell = (q, r)
                mark = "B" if cell in state.black else ("W" if cell in state.white else ".")
                tokens.append("q%s=%s" % (_encode_int(q), mark))
            lines.append("r%s:%s" % (_encode_int(r), " ".join(tokens)))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        cells, dir_name = _parse_action_name(action)
        return _format_action(cells, dir_name)

    def name_to_action(self, name: str) -> str:
        canonical = self.action_to_name(name)
        if canonical != name:
            raise ValueError("not a canonical action name")
        return name

    def _winner(self, state: GameState) -> Optional[int]:
        if state.winner is not None:
            return state.winner
        b, w = state.pushed_off_by
        if b >= self.target_pushed and w < self.target_pushed:
            return BLACK
        if w >= self.target_pushed and b < self.target_pushed:
            return WHITE
        return None

    def _score_terminal(self, state: GameState) -> bool:
        return (
            state.winner is not None
            or state.pushed_off_by[BLACK] >= self.target_pushed
            or state.pushed_off_by[WHITE] >= self.target_pushed
        )

    def _player_cells(self, state: GameState, player: int) -> FrozenSet[Cell]:
        if player == BLACK:
            return state.black
        if player == WHITE:
            return state.white
        return frozenset()

    def _legal_action_names(self, state: GameState) -> List[str]:
        if self._score_terminal(state) or state.current not in (BLACK, WHITE):
            return []
        own = self._player_cells(state, state.current)
        actions: Set[str] = set()
        for group in self._groups(own):
            for dir_name, delta in DIRECTIONS:
                if self._can_move(state, group, delta):
                    actions.add(_format_action(group, dir_name))
        return sorted(actions)

    def _groups(self, own: FrozenSet[Cell]) -> List[Tuple[Cell, ...]]:
        groups: Set[FrozenSet[Cell]] = set()
        for cell in own:
            groups.add(frozenset((cell,)))
        for axis in AXES:
            for cell in own:
                for length in (2, 3):
                    seq = tuple(_add(cell, axis, i) for i in range(length))
                    if all(c in own for c in seq):
                        groups.add(frozenset(seq))
        return sorted(
            (tuple(sorted(g, key=_cell_label)) for g in groups),
            key=lambda g: (len(g), ",".join(_cell_label(c) for c in g)),
        )

    def _group_axis(self, group: Iterable[Cell]) -> Optional[Direction]:
        group_set = frozenset(group)
        n = len(group_set)
        if n <= 1:
            return None
        for axis in AXES:
            for start in group_set:
                if frozenset(_add(start, axis, i) for i in range(n)) == group_set:
                    return axis
        return None

    def _front_cell(self, group: Iterable[Cell], delta: Direction) -> Cell:
        group_set = frozenset(group)
        fronts = [c for c in group_set if _add(c, delta) not in group_set]
        if len(fronts) != 1:
            raise ValueError("group has no unique front in this direction")
        return fronts[0]

    def _opponent_line(
        self, opponent_cells: Iterable[Cell], start: Cell, delta: Direction
    ) -> Tuple[List[Cell], Cell]:
        opponent_set = set(opponent_cells)
        line: List[Cell] = []
        cursor = start
        while cursor in opponent_set:
            line.append(cursor)
            cursor = _add(cursor, delta)
        return line, cursor

    def _can_move(self, state: GameState, group: Iterable[Cell], delta: Direction) -> bool:
        group_set = frozenset(group)
        if not 1 <= len(group_set) <= 3:
            return False

        player = state.current
        own = self._player_cells(state, player)
        opponent = self._player_cells(state, WHITE if player == BLACK else BLACK)
        occupied = state.black | state.white

        if not group_set <= own:
            return False

        if len(group_set) == 1:
            dest = _add(next(iter(group_set)), delta)
            return dest in self.cells and dest not in occupied

        axis = self._group_axis(group_set)
        if axis is None:
            return False

        inline = delta == axis or delta == _neg(axis)

        if not inline:
            # Side movement: every selected ball moves into a free adjacent hole.
            return all(_add(c, delta) in self.cells and _add(c, delta) not in occupied for c in group_set)

        front = self._front_cell(group_set, delta)
        dest = _add(front, delta)

        if dest not in self.cells:
            return False
        if dest not in occupied:
            return True
        if dest in own:
            return False

        # Sumito: straight-line push only, attacker count must exceed defender count.
        opp_line, after = self._opponent_line(opponent, dest, delta)
        if len(group_set) <= len(opp_line):
            return False
        if len(opp_line) > 2:
            return False

        # Behind the attacked balls must be empty, or off-board for pushing out.
        if after in self.cells:
            return after not in occupied
        return True
