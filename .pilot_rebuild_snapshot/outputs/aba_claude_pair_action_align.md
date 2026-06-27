```python
# --- sentinels (OpenSpiel-style) -------------------------------------------
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

# --- board geometry --------------------------------------------------------
ROW_SIZES = [5, 6, 7, 8, 9, 8, 7, 6, 5]          # rows 0..8  == letters A..I
DIRECTIONS = ['E', 'W', 'NE', 'NW', 'SE', 'SW']
OPPOSITE = {'E': 'W', 'W': 'E', 'NE': 'SW', 'SW': 'NE', 'NW': 'SE', 'SE': 'NW'}
POSITIVE_DIRS = ['E', 'NE', 'NW']                # one direction per axis (avoids dup groups)

MAX_PLIES = 1000                                 # finiteness safeguard, not a real rule


def on_board(row, col):
    return 0 <= row <= 8 and 0 <= col < ROW_SIZES[row]


def neighbor(cell, d):
    """Neighbouring cell in direction d (may be off-board; caller checks on_board)."""
    row, col = cell
    if d == 'E':
        return (row, col + 1)
    if d == 'W':
        return (row, col - 1)
    if d == 'NE':                                # row above; wider iff row <= 3
        return (row + 1, col + 1) if row <= 3 else (row + 1, col)
    if d == 'NW':
        return (row + 1, col) if row <= 3 else (row + 1, col - 1)
    if d == 'SE':                                # row below; wider iff row >= 5
        return (row - 1, col + 1) if row >= 5 else (row - 1, col)
    if d == 'SW':
        return (row - 1, col) if row >= 5 else (row - 1, col - 1)
    raise ValueError("bad direction: %r" % (d,))


def cell_to_label(cell):
    # Shared BoardBench labelling: row letters A (top) .. I (bottom).
    # Internal row 0 is the bottom row, so the letter index is mirrored (8 - row).
    row, col = cell
    return "%s%d" % (chr(ord('A') + (8 - row)), col + 1)


def label_to_cell(label):
    row = 8 - (ord(label[0]) - ord('A'))
    col = int(label[1:]) - 1
    return (row, col)


def chain_along(cells_set, ad):
    """If the cells form a contiguous straight chain in direction ad, return it
    ordered (front = last); else None."""
    n = len(cells_set)
    for start in cells_set:
        chain = [start]
        cur = start
        for _ in range(n - 1):
            nxt = neighbor(cur, ad)
            if nxt not in cells_set:
                break
            chain.append(nxt)
            cur = nxt
        if len(chain) == n:
            return chain
    return None


# --- move resolution (shared by legal_actions and apply_action) ------------
def _resolve(state, cells, d):
    """Return (new_board, off_player) if (cells, d) is a legal move, else None.

    new_board: dict {(row,col): player}.  off_player: the player whose ball was
    pushed off the board this move (only via Sumito), or None.
    """
    board = state.board
    player = state.to_move
    opp = 1 - player
    cells = tuple(cells)

    for c in cells:
        if board.get(c) != player:              # must be own balls
            return None
    k = len(cells)
    if k == 0 or k > 3:
        return None

    # --- single ball: only into an empty on-board cell (never pushes) ------
    if k == 1:
        c = cells[0]
        t = neighbor(c, d)
        if (not on_board(*t)) or (t in board):
            return None
        nb = dict(board)
        del nb[c]
        nb[t] = player
        return (nb, None)

    # --- 2 or 3 balls: must be a straight contiguous line -----------------
    cells_set = set(cells)
    axis_dir = None
    for ad in POSITIVE_DIRS:
        if chain_along(cells_set, ad) is not None:
            axis_dir = ad
            break
    if axis_dir is None:
        return None

    if d in (axis_dir, OPPOSITE[axis_dir]):
        # ---------------- in-line move (may push = Sumito) ----------------
        ordered = chain_along(cells_set, d)      # front = last in direction d
        if ordered is None:
            return None
        front_cell = neighbor(ordered[-1], d)

        if not on_board(*front_cell):
            return None                          # cannot move own ball off board
        if front_cell not in board:
            nb = dict(board)                     # slide into empty cell
            for c in cells:
                del nb[c]
            for c in cells:
                nb[neighbor(c, d)] = player
            return (nb, None)
        if board[front_cell] == player:
            return None                          # blocked by own ball

        # opponent ahead -> attempt Sumito
        defenders = []
        cur = front_cell
        while on_board(*cur) and board.get(cur) == opp:
            defenders.append(cur)
            cur = neighbor(cur, d)
        m = len(defenders)
        if k <= m:                               # need strict majority (Patt otherwise)
            return None
        beyond = cur
        if on_board(*beyond) and (beyond in board):
            return None                          # own ball behind defenders -> no free space

        nb = dict(board)
        for c in cells:
            del nb[c]
        for c in defenders:
            del nb[c]
        off_player = None
        for c in defenders:                      # only the lead defender can leave the board
            t = neighbor(c, d)
            if on_board(*t):
                nb[t] = opp
            else:
                off_player = opp
        for c in cells:
            nb[neighbor(c, d)] = player
        return (nb, off_player)

    # ---------------- broadside move (never pushes) -----------------------
    dests = []
    for c in cells:
        t = neighbor(c, d)
        if (not on_board(*t)) or (t in board):
            return None
        dests.append(t)
    nb = dict(board)
    for c in cells:
        del nb[c]
    for t in dests:
        nb[t] = player
    return (nb, None)


# --- state -----------------------------------------------------------------
class GameState:
    """Public, fully-observable state. apply_action returns a fresh state."""

    def __init__(self, board, to_move, off, ply):
        self.board = board          # dict {(row,col): 0|1}; empty cells absent
        self.to_move = to_move      # 0 = Black, 1 = White
        self.off = off              # [black balls pushed out, white balls pushed out]
        self.ply = ply

    def copy(self):
        return GameState(dict(self.board), self.to_move, list(self.off), self.ply)

    def __eq__(self, other):
        return (isinstance(other, GameState) and self.to_move == other.to_move
                and self.off == other.off and self.ply == other.ply
                and self.board == other.board)

    def __hash__(self):
        return hash((frozenset(self.board.items()), self.to_move,
                     tuple(self.off), self.ply))


# --- game ------------------------------------------------------------------
class Game:
    num_players = 2

    def initial_state(self):
        # ASSUMPTION: standard Abalone opening (Abb. 1 not provided).
        board = {}
        for col in range(ROW_SIZES[8]):          # Black: row I (top)
            board[(8, col)] = 0
        for col in range(ROW_SIZES[7]):          # Black: row H
            board[(7, col)] = 0
        for col in (2, 3, 4):                    # Black: centre three of row G
            board[(6, col)] = 0
        for col in range(ROW_SIZES[0]):          # White: row A (bottom)
            board[(0, col)] = 1
        for col in range(ROW_SIZES[1]):          # White: row B
            board[(1, col)] = 1
        for col in (2, 3, 4):                    # White: centre three of row C
            board[(2, col)] = 1
        return GameState(board, 0, [0, 0], 0)    # Black moves first

    # -- queries --
    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        return state.to_move

    def _gen_actions(self, state):
        player = state.to_move
        board = state.board
        own = [c for c, p in board.items() if p == player]
        own_set = set(own)
        found = set()
        for c in own:                            # single-ball moves
            for d in DIRECTIONS:
                if _resolve(state, (c,), d) is not None:
                    found.add(((c,), d))
        for c in own:                            # 2- and 3-ball lines (each enumerated once)
            for ad in POSITIVE_DIRS:
                n1 = neighbor(c, ad)
                if n1 in own_set:
                    g2 = tuple(sorted((c, n1)))
                    for d in DIRECTIONS:
                        if _resolve(state, g2, d) is not None:
                            found.add((g2, d))
                    n2 = neighbor(n1, ad)
                    if n2 in own_set:
                        g3 = tuple(sorted((c, n1, n2)))
                        for d in DIRECTIONS:
                            if _resolve(state, g3, d) is not None:
                                found.add((g3, d))
        return sorted(found)

    def is_terminal(self, state):
        if state.off[0] >= 6 or state.off[1] >= 6:
            return True
        if state.ply >= MAX_PLIES:
            return True
        return len(self._gen_actions(state)) == 0   # stuck player (rules silent -> draw)

    def legal_actions(self, state):
        if state.off[0] >= 6 or state.off[1] >= 6:
            return []
        if state.ply >= MAX_PLIES:
            return []
        return self._gen_actions(state)

    def returns(self, state):
        if state.off[1] >= 6:                    # 6 White balls out -> Black wins
            return [1.0, -1.0]
        if state.off[0] >= 6:                    # 6 Black balls out -> White wins
            return [-1.0, 1.0]
        return [0.0, 0.0]                        # ongoing, ply-cap draw, or stuck draw

    # -- transition --
    def apply_action(self, state, action):
        cells, d = action
        res = _resolve(state, cells, d)
        if res is None:
            raise ValueError("illegal action: %s" % (self.action_to_name(action),))
        new_board, off_player = res
        new_off = list(state.off)
        if off_player is not None:
            new_off[off_player] += 1
        return GameState(new_board, 1 - state.to_move, new_off, state.ply + 1)

    # -- naming (shared BoardBench scheme; round-trips exactly) --
    def action_to_name(self, action):
        # Cells top-to-bottom, left-to-right, concatenated with no separator and
        # joined to DIR by "->". The concatenation is intentional: a separator
        # between two cell labels would let the BoardBench normalizer read them
        # as a source->target route and drop DIR, collapsing distinct moves.
        cells, d = action
        ordered = sorted(cells, key=lambda c: (8 - c[0], c[1]))
        return "move:" + "".join(cell_to_label(c) for c in ordered) + "->" + d

    def name_to_action(self, name):
        body = name[5:] if name.startswith("move:") else name
        labels_part, d = body.split("->")
        labels = [labels_part[i:i + 2] for i in range(0, len(labels_part), 2)]
        cells = tuple(sorted(label_to_cell(lbl) for lbl in labels))
        return (cells, d)

    # -- rendering (deterministic, compact, hexagon-shaped) --
    def render(self, state):
        sym = {0: 'b', 1: 'w'}
        lines = ["to_move: %d (%s)  out: black=%d white=%d  ply=%d"
                 % (state.to_move, sym[state.to_move],
                    state.off[0], state.off[1], state.ply)]
        for row in range(8, -1, -1):             # I (top) down to A (bottom)
            letter = chr(ord('A') + row)
            lead = " " * abs(row - 4)            # indent to draw the hexagon
            cells = []
            for col in range(ROW_SIZES[row]):
                p = state.board.get((row, col))
                cells.append(sym[p] if p is not None else '.')
            lines.append("%s %s%s" % (letter, lead, " ".join(cells)))
        return "\n".join(lines)


if __name__ == "__main__":
    g = Game()
    s = g.initial_state()
    print(g.render(s))
    for _ in range(6):
        if g.is_terminal(s):
            break
        a = g.legal_actions(s)[0]                # deterministic demo: first legal action
        nm = g.action_to_name(a)
        assert g.name_to_action(nm) == a, "round-trip failed"
        s = g.apply_action(s, a)
        print("\nmove:", nm)
        print(g.render(s))
    print("\nterminal:", g.is_terminal(s), " returns:", g.returns(s))
```

```python
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
Each integer has a unique human-readable name in the shared BoardBench scheme,
e.g. "move:C3C4C5->E".
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
# shapes, sort by a canonical internal key and assign each a stable integer id.
# ---------------------------------------------------------------------------

def _move_name(group, d):
    # Internal id-stable sort key only (NOT the emitted name; see _display_name).
    # Kept unchanged so the integer action ids stay identical to before.
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
    assert len(name_to_id) == len(id_to_name), "non-unique internal keys"
    return id_to_move, id_to_name, name_to_id


def _display_name(group, d):
    """Shared BoardBench action name: 'move:<cells>->DIR'.

    Cells use the same A(top)..I(bottom) labels as _label, listed top-to-bottom
    then left-to-right and concatenated with NO separator so the BoardBench
    normalizer keeps DIR. A separator between two cell labels would let it read
    them as a source->target route and drop DIR. This pairs with the oneshot
    variant, which emits byte-identical names.
    """
    ordered = sorted(group, key=lambda c: (c[2], c[0]))
    return "move:" + "".join(_label(c) for c in ordered) + "->" + d


# ID_TO_MOVE / the integer action ids keep their original (_move_name-sorted)
# order, so legal_actions returns exactly the same ids as before; only the
# human-readable names are re-skinned into the shared comparison language.
ID_TO_MOVE = _enumerate_moves()[0]
ID_TO_NAME = [_display_name(g, d) for (g, d, _k) in ID_TO_MOVE]
NAME_TO_ID = {nm: i for i, nm in enumerate(ID_TO_NAME)}
assert len(NAME_TO_ID) == len(ID_TO_NAME), "non-unique action names"
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

    # -- naming (shared BoardBench scheme) ---------------------------------

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
```
