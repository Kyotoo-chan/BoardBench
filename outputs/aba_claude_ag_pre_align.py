"""Abalone (2-player) - self-contained reference implementation.

Source of truth: the supplied German rulebook ("Abalone quattro", 2-Spieler
rules) text plus its figures (especially Abbildung 1, the starting position).
Only standard library is used. No outside game knowledge was assumed beyond
what the rule text and figures state.

Rules implemented (from the rulebook):
  * Goal: be the first to push SIX of the opponent's balls off the board
    ("Als erster Spieler sechs Kugeln des Gegners vom Spielfeld zu schieben").
  * Black starts ("Schwarz faengt immer an"); players alternate.
  * A turn moves 1, 2 or 3 of your OWN balls that lie in a straight contiguous
    line, exactly one step, into one of the six directions.
  * Two move kinds:
      - In-line ("Bewegung in gerader Linie"): move along the line. May push
        opponent balls (Sumito) if you have a strict majority (k > m) in that
        line, the balls are directly adjacent with no gap, lie on one straight
        line, and the cell behind the pushed group is free OR off the board
        (off the board => that ball is captured).
      - Broadside ("Bewegung zur Seite"): move the line sideways. Every
        destination cell must be empty; broadside can NEVER push.
  * Sumito kinds 2-vs-1, 3-vs-1, 3-vs-2 follow from k > m with k,m <= 3.
  * Patt (equal numbers, e.g. 1-1/2-2/3-3) is automatic: k > m fails, no push.
  * A ball pushed off the board is out ("Hinausschieben"). Six out => loss.

Board / starting layout taken from Abbildung 1:
  * Hexagonal board, 61 cells, row sizes 5,6,7,8,9,8,7,6,5.
  * Each side has 14 balls in the classic layout (two full back rows + the
    centred three of the next row). Black occupies the top, White the bottom.

Documented ASSUMPTIONS (the rulebook does NOT specify these; see "Open
questions / assumptions" in the accompanying notes):
  * Coordinate labels are invented for readability. Rows are lettered A (top)
    to I (bottom); columns are numbered 1.. from left to right within a row.
    The rulebook defines no labels, so these are ours.
  * The rulebook gives no draw rule and uses a chess clock for termination
    ("Gegen die Zeit"), which is not a discrete game rule. To avoid unbounded
    games we add a ply cap (default 400). Reaching it with nobody at six
    captures is scored as a draw [0, 0]. This safeguard is NOT in the rulebook.
  * We assume a player always has at least one legal move (true for any
    reachable Abalone position with 8-14 balls on 61 cells); no "pass" exists.

Public API:
  GameState, Game, Game.initial_state/current_player/legal_actions/apply_action/
  is_terminal/returns/render/action_to_name/name_to_action.

Actions are stable integers indexing a fixed, name-sorted global move table.
Each integer has a unique human-readable name, e.g. "move:C3+C4+C5:E".
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TERMINAL = -1            # sentinel returned by current_player at terminal nodes

BLACK = 0
WHITE = 1
NUM_PLAYERS = 2

CAPTURE_TARGET = 6                 # six opponent balls pushed off => win
BOARD_RADIUS = 4                   # hexagon "radius" in cube coords -> 61 cells
DEFAULT_MAX_MOVES = 400            # anti-infinite-game safeguard (see notes)

# The six neighbour directions as cube-coordinate deltas (x + y + z == 0).
# A horizontal row is a line of constant z; E/W stay in the row.
DIRS = {
    'E':  (1, -1, 0),
    'W':  (-1, 1, 0),
    'NE': (1, 0, -1),
    'SW': (-1, 0, 1),
    'NW': (0, 1, -1),
    'SE': (0, -1, 1),
}
OPP_DIR = {'E': 'W', 'W': 'E', 'NE': 'SW', 'SW': 'NE', 'NW': 'SE', 'SE': 'NW'}
# One representative ("positive") direction per line orientation.
POS_DIRS = ('E', 'NE', 'NW')

ROW_LETTERS = "ABCDEFGHI"          # z = -4..4  ->  A..I (top..bottom)


# ---------------------------------------------------------------------------
# Cell geometry
# ---------------------------------------------------------------------------

def _xmin(z):
    return max(-BOARD_RADIUS, -BOARD_RADIUS - z)


def _xmax(z):
    return min(BOARD_RADIUS, BOARD_RADIUS - z)


def _build_cells():
    cells = []
    for z in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
        for x in range(_xmin(z), _xmax(z) + 1):
            cells.append((x, -x - z, z))
    return cells


CELLS = _build_cells()                 # 61 cube coordinates
CELLSET = frozenset(CELLS)


def _add(cell, d):
    dx, dy, dz = DIRS[d]
    return (cell[0] + dx, cell[1] + dy, cell[2] + dz)


def _label(cell):
    """Cube cell -> human label like 'C5' (row letter + 1-based column)."""
    x, _, z = cell
    return ROW_LETTERS[z + BOARD_RADIUS] + str(x - _xmin(z) + 1)


def _unlabel(text):
    """Inverse of _label: 'C5' -> cube cell."""
    z = ROW_LETTERS.index(text[0]) - BOARD_RADIUS
    x = _xmin(z) + int(text[1:]) - 1
    return (x, -x - z, z)


# ---------------------------------------------------------------------------
# Starting position (read off Abbildung 1; symmetric, 14 balls each)
# ---------------------------------------------------------------------------

BLACK_START = tuple(_unlabel(s) for s in (
    'A1', 'A2', 'A3', 'A4', 'A5',
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6',
    'C3', 'C4', 'C5'))
WHITE_START = tuple(_unlabel(s) for s in (
    'I1', 'I2', 'I3', 'I4', 'I5',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'G3', 'G4', 'G5'))


# ---------------------------------------------------------------------------
# Global move table.
#
# A move is fully described by (group of own cells, direction).  We enumerate
# every geometrically-possible such move once, keep only "potentially legal"
# shapes, sort by canonical name and assign each a stable integer id.
# ---------------------------------------------------------------------------

def _move_name(group, d):
    ordered = sorted(group, key=lambda c: (c[2], c[0]))
    return "move:" + "+".join(_label(c) for c in ordered) + ":" + d


def _enumerate_moves():
    raw = []

    # Singletons: one ball, any of the 6 directions into an on-board cell.
    for c in CELLS:
        for d in DIRS:
            if _add(c, d) in CELLSET:
                raw.append((tuple([c]), d, 'inline'))

    # Lines of 2 and 3 along each orientation (generated once, from the low end).
    for axis in POS_DIRS:
        back = OPP_DIR[axis]
        for c in CELLS:
            line = [c]
            for _ in range(2):
                nxt = _add(line[-1], axis)
                if nxt in CELLSET:
                    line.append(nxt)
                else:
                    break
            for length in (2, 3):
                if len(line) < length:
                    continue
                group = tuple(line[:length])
                # In-line forward (along axis): keep only if the front cell is
                # on the board (otherwise it could only push an own ball off).
                if _add(group[-1], axis) in CELLSET:
                    raw.append((group, axis, 'inline'))
                # In-line backward (along -axis).
                if _add(group[0], back) in CELLSET:
                    raw.append((group, back, 'inline'))
                # Broadside: the 4 directions not parallel to the axis; keep
                # only if every destination is on the board.
                for d in DIRS:
                    if d == axis or d == back:
                        continue
                    if all(_add(cell, d) in CELLSET for cell in group):
                        raw.append((group, d, 'broadside'))

    named = sorted(((_move_name(g, d), g, d, k) for (g, d, k) in raw),
                   key=lambda t: t[0])
    id_to_move = [(g, d, k) for (_, g, d, k) in named]
    id_to_name = [nm for (nm, _, _, _) in named]
    name_to_id = {nm: i for i, nm in enumerate(id_to_name)}
    assert len(name_to_id) == len(id_to_name), "non-unique action names"
    return id_to_move, id_to_name, name_to_id


ID_TO_MOVE, ID_TO_NAME, NAME_TO_ID = _enumerate_moves()
NUM_DISTINCT_ACTIONS = len(ID_TO_MOVE)


# ---------------------------------------------------------------------------
# Move legality / application as pure functions of the board
# ---------------------------------------------------------------------------

def _inline_lead(group, d):
    """The cell of an in-line group that exits the group when stepping +d."""
    gset = set(group)
    for c in group:
        if _add(c, d) not in gset:
            return c
    return group[0]  # unreachable for a straight group


def _push_run(board, start, opp, d):
    """Count consecutive opponent balls from `start` along d; return (m, end)."""
    m = 0
    c = start
    while c in CELLSET and board.get(c) == opp:
        m += 1
        c = _add(c, d)
    return m, c


def _legal(board, player, group, d, kind):
    for c in group:
        if board.get(c) != player:
            return False

    if kind == 'broadside':
        for c in group:
            t = _add(c, d)
            if t not in CELLSET or board.get(t) is not None:
                return False
        return True

    # in-line
    front = _add(_inline_lead(group, d), d)
    if front not in CELLSET:
        return False
    occ = board.get(front)
    if occ is None:
        return True                       # slide into the free hollow
    if occ == player:
        return False                      # cannot push own balls
    # Sumito: strict majority and a free hollow (or the edge) behind them.
    opp = 1 - player
    m, end = _push_run(board, front, opp, d)
    if len(group) > m and (end not in CELLSET or board.get(end) is None):
        return True
    return False


# ---------------------------------------------------------------------------
# State and Game
# ---------------------------------------------------------------------------

class GameState:
    """Mutable game state. `apply_action` returns a fresh clone (no mutation
    of the argument)."""

    __slots__ = ('board', 'to_move', 'off', 'ply')

    def __init__(self, board, to_move, off, ply):
        self.board = board        # dict: cell -> BLACK/WHITE (absent => empty)
        self.to_move = to_move    # BLACK or WHITE
        self.off = off            # [black_balls_off, white_balls_off]
        self.ply = ply            # number of moves played

    def clone(self):
        return GameState(dict(self.board), self.to_move, list(self.off), self.ply)

    def __eq__(self, other):
        return (isinstance(other, GameState)
                and self.board == other.board
                and self.to_move == other.to_move
                and self.off == other.off
                and self.ply == other.ply)

    def __hash__(self):
        return hash((frozenset(self.board.items()), self.to_move,
                     tuple(self.off), self.ply))


class Game:
    def __init__(self, max_moves=DEFAULT_MAX_MOVES):
        self.num_players = NUM_PLAYERS
        self.max_moves = max_moves
        self.num_distinct_actions = NUM_DISTINCT_ACTIONS

    # -- core API ----------------------------------------------------------

    def initial_state(self):
        board = {}
        for c in BLACK_START:
            board[c] = BLACK
        for c in WHITE_START:
            board[c] = WHITE
        return GameState(board, BLACK, [0, 0], 0)

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        return state.to_move

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        board, player = state.board, state.to_move
        return [i for i, (g, d, k) in enumerate(ID_TO_MOVE)
                if _legal(board, player, g, d, k)]

    def apply_action(self, state, action):
        group, d, kind = ID_TO_MOVE[action]
        player = state.to_move
        if not _legal(state.board, player, group, d, kind):
            raise ValueError("illegal action: %s" % self.action_to_name(action))

        ns = state.clone()
        board = ns.board
        opp = 1 - player

        if kind == 'broadside':
            for c in group:
                del board[c]
            for c in group:
                board[_add(c, d)] = player
        else:
            front = _add(_inline_lead(group, d), d)
            if board.get(front) is None:
                for c in group:
                    del board[c]
                for c in group:
                    board[_add(c, d)] = player
            else:
                m, _ = _push_run(board, front, opp, d)
                for c in group:
                    del board[c]
                c = front
                for _ in range(m):
                    del board[c]
                    c = _add(c, d)
                for c in group:
                    board[_add(c, d)] = player
                c = front
                for _ in range(m):
                    dst = _add(c, d)
                    if dst in CELLSET:
                        board[dst] = opp
                    else:
                        ns.off[opp] += 1       # pushed off the board => captured
                    c = dst

        ns.to_move = opp
        ns.ply += 1
        return ns

    def is_terminal(self, state):
        return (state.off[WHITE] >= CAPTURE_TARGET
                or state.off[BLACK] >= CAPTURE_TARGET
                or state.ply >= self.max_moves)

    def returns(self, state):
        if state.off[WHITE] >= CAPTURE_TARGET:   # Black pushed 6 White balls off
            return [1.0, -1.0]
        if state.off[BLACK] >= CAPTURE_TARGET:
            return [-1.0, 1.0]
        return [0.0, 0.0]                        # non-terminal or draw at ply cap

    # -- naming ------------------------------------------------------------

    def action_to_name(self, action):
        return ID_TO_NAME[action]

    def name_to_action(self, name):
        return NAME_TO_ID[name]

    # -- rendering ---------------------------------------------------------

    def render(self, state):
        sym = {BLACK: 'b', WHITE: 'w', None: '.'}
        if self.is_terminal(state):
            r = self.returns(state)
            status = ('Black wins' if r == [1.0, -1.0]
                      else 'White wins' if r == [-1.0, 1.0]
                      else 'draw')
            head = ("Abalone ply=%d TERMINAL(%s) off B:%d W:%d"
                    % (state.ply, status, state.off[BLACK], state.off[WHITE]))
        else:
            tm = 'Black' if state.to_move == BLACK else 'White'
            head = ("Abalone ply=%d to_move=%s off B:%d W:%d"
                    % (state.ply, tm, state.off[BLACK], state.off[WHITE]))
        lines = [head]
        for z in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
            indent = 2 * _xmin(z) + z + 2 * BOARD_RADIUS
            row = [sym[state.board.get((x, -x - z, z))]
                   for x in range(_xmin(z), _xmax(z) + 1)]
            lines.append(ROW_LETTERS[z + BOARD_RADIUS]
                         + " " * (indent + 1) + " ".join(row))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Minimal self-check (only runs when executed directly, not on import).
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    g = Game()
    s = g.initial_state()
    print(g.render(s))
    acts = g.legal_actions(s)
    print("legal opening moves:", len(acts))
    print("distinct actions:", g.num_distinct_actions)
    # round-trip every legal action name
    for a in acts:
        assert g.name_to_action(g.action_to_name(a)) == a
    print("sample:", g.action_to_name(acts[0]))
