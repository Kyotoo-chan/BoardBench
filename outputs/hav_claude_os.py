"""
Havannah (Christian Freeling / Ravensburger) -- single self-contained file,
standard library only, following the OpenSpiel-inspired BoardBench backbone.

Rules source: the 3 supplied rulebook page images (German). Only page 1 carries
actual rules; pages 2-3 are strategy/tactics commentary and add no mechanics.

Rules used (page 1):
  * Board: 169 intersection points forming a hexagon. 169 = 3*R^2+3*R+1 with
    R=7 (hexagon of side length 8). Modeled in cube coordinates (x, y, z),
    x+y+z == 0, each coordinate in [-7, 7].
  * 2 players, Red and Black. "Rot faengt an" -> Red moves first.
  * Players alternately place one stone on any empty point.
  * A player wins immediately by completing, within ONE connected single-colour
    group (stone next to stone, no gap, not interrupted by the other colour),
    one of three figures:
      - Ring  : a closed loop enclosing at least one point (enclosed point(s)
                may be empty, own or enemy).
      - Bridge: a connection joining any two of the six corner points.
      - Fork  : a connection joining any three of the six sides. Corner points
                do NOT belong to the sides.

Assumptions (rulebook silent / scan unclear) -- see also the answer text:
  * Colour draw not modeled; Red is fixed as player 0 and moves first.
  * Explicit axial q/r action notation defined here (board image has none).
  * Board full with no figure -> draw (standard for connection games).
  * Physical stone supply (~55/56) not enforced.
  * Only the player who just moved can create a figure.
"""

# ---- backbone sentinels -----------------------------------------------------
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

# ---- game constants ---------------------------------------------------------
BOARD_RADIUS = 7          # 169 points = 3*R^2 + 3*R + 1 with R = 7 (side 8)
NUM_PLAYERS = 2
RED, BLACK = 0, 1
_SYM = {RED: 'R', BLACK: 'B'}

# six hex directions in cube coordinates
_DIRS = ((1, -1, 0), (1, 0, -1), (0, 1, -1), (-1, 1, 0), (-1, 0, 1), (0, -1, 1))


# ---- geometry helpers (module-level, pure) ----------------------------------
def _all_cells():
    R = BOARD_RADIUS
    cells = []
    for x in range(-R, R + 1):
        for y in range(-R, R + 1):
            z = -x - y
            if -R <= z <= R:
                cells.append((x, y, z))
    return cells


def _on_board(cell):
    x, y, z = cell
    R = BOARD_RADIUS
    return x + y + z == 0 and -R <= x <= R and -R <= y <= R and -R <= z <= R


def _neighbors(cell):
    x, y, z = cell
    out = []
    for dx, dy, dz in _DIRS:
        n = (x + dx, y + dy, z + dz)
        if _on_board(n):
            out.append(n)
    return out


def _extremes(cell):
    """Side labels whose coordinate is at +/-R for this cell."""
    x, y, z = cell
    R = BOARD_RADIUS
    ex = []
    if x == R: ex.append('xp')
    if x == -R: ex.append('xn')
    if y == R: ex.append('yp')
    if y == -R: ex.append('yn')
    if z == R: ex.append('zp')
    if z == -R: ex.append('zn')
    return ex


def _is_corner(cell):
    # corner cells satisfy exactly two extreme conditions
    return len(_extremes(cell)) == 2


def _side_of(cell):
    # a non-corner boundary cell lies on exactly one side; else None
    ex = _extremes(cell)
    return ex[0] if len(ex) == 1 else None


def _enc(v):
    if v > 0: return 'p' + str(v)
    if v < 0: return 'n' + str(-v)
    return '0'


def _dec(tok):
    if tok == '0': return 0
    if tok and tok[0] == 'p': return int(tok[1:])
    if tok and tok[0] == 'n': return -int(tok[1:])
    raise ValueError("bad coordinate token: %r" % tok)


# ---- state ------------------------------------------------------------------
class GameState:
    """Full, public game state (perfect information)."""
    __slots__ = ('board', 'to_move', 'winner', 'num_moves')

    def __init__(self, board=None, to_move=RED, winner=None, num_moves=0):
        self.board = board if board is not None else {}  # cell -> RED/BLACK
        self.to_move = to_move
        self.winner = winner          # None, RED, BLACK, or 'draw'
        self.num_moves = num_moves

    def copy(self):
        return GameState(dict(self.board), self.to_move, self.winner, self.num_moves)


# ---- game -------------------------------------------------------------------
class Game:
    def __init__(self):
        self.num_players = NUM_PLAYERS
        self._cells = _all_cells()            # fixed, deterministic order
        self._cell_set = set(self._cells)
        self._corners = [c for c in self._cells if _is_corner(c)]

    # -- backbone API --------------------------------------------------------
    def initial_state(self):
        return GameState()

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        return state.to_move

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        occ = state.board
        return [c for c in self._cells if c not in occ]

    def apply_action(self, state, action):
        """Return a NEW state; the input state is not mutated."""
        if self.is_terminal(state):
            raise ValueError("game is already over")
        if action not in self._cell_set:
            raise ValueError("action is off-board: %r" % (action,))
        if action in state.board:
            raise ValueError("point already occupied: %r" % (action,))
        ns = state.copy()
        mover = ns.to_move
        ns.board[action] = mover
        ns.num_moves += 1
        if self._has_win(ns, mover):
            ns.winner = mover
        elif len(ns.board) == len(self._cells):
            ns.winner = 'draw'
        ns.to_move = BLACK if mover == RED else RED
        return ns

    def is_terminal(self, state):
        return state.winner is not None

    def returns(self, state):
        """One value per player; only meaningful at terminal states."""
        w = state.winner
        if w == RED:
            return [1.0, -1.0]
        if w == BLACK:
            return [-1.0, 1.0]
        return [0.0, 0.0]   # non-terminal or draw

    def render(self, state):
        R = BOARD_RADIUS
        if state.winner is None:
            wtxt = '-'
        elif state.winner == 'draw':
            wtxt = 'draw'
        else:
            figs = self._winning_figures(state, state.winner)
            wtxt = '%s(%s)' % (_SYM[state.winner], '+'.join(figs) if figs else '?')
        lines = ["Havannah  move#%d  to_move=%s  winner=%s"
                 % (state.num_moves, _SYM[state.to_move], wtxt)]
        width = 2 * R + 1
        for z in range(-R, R + 1):
            xmin = max(-R, -R - z)
            xmax = min(R, R - z)
            row = []
            for x in range(xmin, xmax + 1):
                cell = (x, -z - x, z)
                p = state.board.get(cell)
                if p is not None:
                    row.append(_SYM[p])
                else:
                    row.append('+' if _is_corner(cell) else '.')  # '+' marks corners
            indent = ' ' * (width - (xmax - xmin + 1))
            lines.append(indent + ' '.join(row))
        return '\n'.join(lines)

    def action_to_name(self, action):
        # Shared pair convention (identical in the agentic file): axial q/r
        # labels (q = cube x, r = cube z; the redundant third axis y = -q - r is
        # dropped) emitted as place:q<coord>_r<coord>. This matches the
        # normalizer's q/r hex parser and already equals its own normalized
        # comparison key. Explicit p/n signs keep +n and -n distinct
        # (qp1 vs qn1) instead of colliding; zero is the bare token "0".
        x, y, z = action
        return "place:q%s_r%s" % (_enc(x), _enc(z))

    def name_to_action(self, name):
        if not name.startswith("place:"):
            raise ValueError("bad action name: %r" % name)
        body = name[6:].replace("_", "")     # robust to punctuation stripping
        if not body or body[0] != 'q':
            raise ValueError("bad action name: %r" % name)
        ri = body.find('r')                  # r-axis label; p/n/digits never contain 'r'
        if ri < 0:
            raise ValueError("bad action name: %r" % name)
        q = _dec(body[1:ri])
        r = _dec(body[ri + 1:])
        cell = (q, -q - r, r)
        if not _on_board(cell):
            raise ValueError("off-board action name: %r" % name)
        return cell

    # -- win detection -------------------------------------------------------
    def _has_win(self, state, color):
        return self._has_bridge_or_fork(state, color) or self._has_ring(state, color)

    def _connected_components(self, state, color):
        stones = {c for c, p in state.board.items() if p == color}
        seen, comps = set(), []
        for s in stones:
            if s in seen:
                continue
            comp, stack = [], [s]
            seen.add(s)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for n in _neighbors(cur):
                    if n in stones and n not in seen:
                        seen.add(n)
                        stack.append(n)
            comps.append(comp)
        return comps

    def _has_bridge_or_fork(self, state, color):
        for comp in self._connected_components(state, color):
            corners, sides = 0, set()
            for c in comp:
                if _is_corner(c):
                    corners += 1
                else:
                    s = _side_of(c)
                    if s:
                        sides.add(s)
            if corners >= 2 or len(sides) >= 3:
                return True
        return False

    def _has_ring(self, state, color):
        """Ring iff some non-`color` cell is enclosed (cannot reach the board
        edge through non-`color` cells)."""
        board = state.board
        R = BOARD_RADIUS
        not_c = [c for c in self._cells if board.get(c) != color]
        not_c_set = set(not_c)
        seen, stack = set(), []
        for c in not_c:                       # seed from boundary cells
            x, y, z = c
            if R in (x, y, z) or -R in (x, y, z):
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
        while stack:
            cur = stack.pop()
            for n in _neighbors(cur):
                if n in not_c_set and n not in seen:
                    seen.add(n)
                    stack.append(n)
        return len(seen) != len(not_c_set)

    def _winning_figures(self, state, color):
        figs = []
        for comp in self._connected_components(state, color):
            corners, sides = 0, set()
            for c in comp:
                if _is_corner(c):
                    corners += 1
                else:
                    s = _side_of(c)
                    if s:
                        sides.add(s)
            if corners >= 2 and 'bridge' not in figs:
                figs.append('bridge')
            if len(sides) >= 3 and 'fork' not in figs:
                figs.append('fork')
        if self._has_ring(state, color) and 'ring' not in figs:
            figs.append('ring')
        return figs
