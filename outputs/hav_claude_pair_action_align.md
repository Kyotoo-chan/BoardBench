## Pair action naming changes

**Shared convention:** `place:q<coord>_r<coord>`, where `<coord>` is `p<k>` (positive), `n<k>` (negative), or bare `0` (zero), with `q` = cube x = axial q and `r` = cube z = axial r. The two coordinate systems already coincide cell-for-cell: left's `(x, z)` projection and right's `(q, r)` cover the identical 169-cell set, and their six neighbour offsets are the same set, so equal labels denote corresponding (adjacency-preserving) cells. This chosen form is exactly the normalizer's canonical q/r key, so in both files `action_to_name(c)` already equals `normalize_action_name(action_to_name(c))`, and is identical across files for the same cell.

**left (oneshot):** logic unchanged — it already used this scheme (underscore separator, `p`/`n`/`0`). Only the naming comment was expanded to mark it as the shared pair convention.

**right (agentic):** `action_to_name` now emits the underscore separator and a bare `0` for zero (was `place:qp1rn6` with no underscore and `p0` for zero). `_sign_token` was renamed to `_coord_token` and now returns `0` for zero. `_NAME_RE` (`_?` optional underscore, `0`/`p0` both accepted) and `_parse_coord` already parsed this form, so round-trip still works and remains backward-compatible.

No legal moves, rules, transitions, scoring, turn order, or chance logic were touched. Within each state every cell has a unique `(q, r)`, so keys never collide.

```python

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


```

```python

"""
Havannah -- self-contained reference implementation.

Source of truth: the provided Havannah rulebook (Ravensburger Spiele Nr.
604 5 126 5, by Christiaan Freeling).  Only mechanics stated in that text are
implemented; the strategy / tactics sections (Rahmen, Magnet, Mühle, tote
Gruppe, ...) are advisory commentary, not rules, and are not modelled.

Rules used (translated from the German rulebook):
  * Board: "169 vertiefte Schnittpunkte" -> a regular hexagon of side 8.
  * Each player owns all stones of one colour; "Rot faengt an" -> Red moves
    first.  Empty start; players alternately place one stone on a free point.
    No capturing and no moving ("Es wird nicht geschlagen und nicht gezogen").
  * Winner is whoever first forms one of three "Sieg-Figuren", each of which is
    a *closed* connection (stone next to stone, no gap, not interrupted by the
    opponent's colour):
        - Ring   : a closed connection that encloses at least one point.  A
                   ring may have any shape/size; it does not matter whether the
                   enclosed points are empty or occupied (by either colour).
        - Bridge : a closed connection between any two of the six corners.
        - Fork   : a closed connection joining any three of the six sides.
                   Corners do NOT belong to the sides.

API (BoardBench / OpenSpiel-inspired backbone), standard library only:
    Game.initial_state(self)
    Game.current_player(self, state)
    Game.legal_actions(self, state)
    Game.apply_action(self, state, action)   -> returns a fresh next state
    Game.is_terminal(self, state)
    Game.returns(self, state)                -> one value per player
    Game.render(self, state)
    Game.action_to_name(self, action)
    Game.name_to_action(self, name)
"""

import re
from collections import deque

# --- sentinels (backbone) -------------------------------------------------
TERMINAL = -1
CHANCE = -2

# --- board geometry -------------------------------------------------------
# Rulebook: 169 intersection points.  A regular hexagon with side S satisfies
# 3*S^2 - 3*S + 1 = cells; S = 8 gives 169.  Equivalent cube-coordinate radius
# R = S - 1 = 7 (3*R^2 + 3*R + 1 = 169).  Cells use axial coords (q, r) with the
# implicit third cube coordinate s = -q - r.
BOARD_SIDE = 8
BOARD_RADIUS = BOARD_SIDE - 1          # = 7
R = BOARD_RADIUS

NUM_PLAYERS = 2
RED = 0                                # Red is the first player ("Rot faengt an").
BLACK = 1
EMPTY = -1
DRAW = "draw"

# Box contents list 55 stones per colour.  This caps each player at 55 placed
# stones (see Assumptions).  With only 110 stones on a 169-point board the cap
# is effectively unreachable before a Sieg-Figur appears, but it bounds the
# game and yields a well-defined draw if it is ever hit.
STONES_PER_PLAYER = 55

PLAYER_CHARS = {EMPTY: ".", RED: "R", BLACK: "B"}
PLAYER_NAMES = {RED: "Red", BLACK: "Black"}

# The 6 neighbour directions in axial (q, r) coordinates.
_DIRS = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)]


def _gen_cells():
    cells = []
    for q in range(-R, R + 1):
        for r in range(-R, R + 1):
            s = -q - r
            if abs(q) <= R and abs(r) <= R and abs(s) <= R:
                cells.append((q, r))
    cells.sort()
    return cells


CELLS = _gen_cells()                        # ordered list of (q, r); len == 169
N = len(CELLS)
CELL_INDEX = {c: i for i, c in enumerate(CELLS)}

# Precomputed adjacency (indices), corner / side / boundary classification.
NEIGHBORS = []
for (_q, _r) in CELLS:
    _nb = []
    for _dq, _dr in _DIRS:
        _j = CELL_INDEX.get((_q + _dq, _r + _dr))
        if _j is not None:
            _nb.append(_j)
    NEIGHBORS.append(tuple(_nb))

CORNER = [False] * N      # True for the 6 corner points
SIDE = [None] * N         # one of 'q+','q-','r+','r-','s+','s-' for non-corner edge points
BOUNDARY = [False] * N    # True for any point on the hex outline (edges + corners)
for _i, (_q, _r) in enumerate(CELLS):
    _s = -_q - _r
    _sat = (abs(_q) == R) + (abs(_r) == R) + (abs(_s) == R)
    BOUNDARY[_i] = _sat >= 1
    if _sat >= 2:
        CORNER[_i] = True                    # two saturated coords -> corner
    elif _sat == 1:                          # exactly one saturated coord -> a side
        if abs(_q) == R:
            SIDE[_i] = "q+" if _q > 0 else "q-"
        elif abs(_r) == R:
            SIDE[_i] = "r+" if _r > 0 else "r-"
        else:
            SIDE[_i] = "s+" if _s > 0 else "s-"


def _coord_token(v):
    # Shared pair convention (identical in the oneshot file): explicit p/n sign
    # letters for non-zero coordinates and a bare "0" for zero.  This matches
    # the normalizer's canonical q/r key, so action_to_name already equals its
    # own normalized comparison form.
    if v > 0:
        return "p" + str(v)
    if v < 0:
        return "n" + str(-v)
    return "0"


def _parse_coord(token):
    """Recover one axial coordinate from an action-name token.

    Accepts the canonical zero ``0`` (now emitted) and the legacy signed zero
    ``p0``/``n0``, plus ``p<k>`` / ``n<k>`` for non-zero magnitudes.  This lets
    name_to_action round-trip both the raw name produced by action_to_name and
    its normalized comparison key, without ever changing which cell a name maps
    to.
    """
    if token == "0":
        return 0
    magnitude = int(token[1:])
    return magnitude if token[0] == "p" else -magnitude


# Shared pair naming: action_to_name emits place:q<coord>_r<coord> with explicit
# p/n sign letters for non-zero coordinates (never +/-, so mirror cells such as
# q=+1 and q=-1 stay distinct after normalization) and a bare 0 for zero
# (e.g. place:qp1_rn6, place:q0_rn7).  The regex stays permissive -- it also
# accepts the underscore-free spelling and a signed p0/n0 zero -- so
# name_to_action round-trips both the raw name and its normalized comparison
# key, never remapping a cell.
_NAME_RE = re.compile(r"^place:q(0|[pn]\d+)_?r(0|[pn]\d+)$")


class GameState:
    """Mutable container for a single Havannah position.

    Fields:
        board       : list[N] of EMPTY / RED / BLACK
        to_move     : RED or BLACK (the player to move next)
        winner      : None (ongoing), RED, BLACK, or DRAW
        stones_left : [red_remaining, black_remaining]
        move_count  : number of stones placed so far
        last_move   : index of the most recent placement, or None
    """

    __slots__ = ("board", "to_move", "winner", "stones_left", "move_count", "last_move")

    def __init__(self, board=None, to_move=RED, winner=None,
                 stones_left=None, move_count=0, last_move=None):
        self.board = [EMPTY] * N if board is None else board
        self.to_move = to_move
        self.winner = winner
        self.stones_left = [STONES_PER_PLAYER, STONES_PER_PLAYER] if stones_left is None else stones_left
        self.move_count = move_count
        self.last_move = last_move

    def copy(self):
        return GameState(list(self.board), self.to_move, self.winner,
                         list(self.stones_left), self.move_count, self.last_move)

    def __repr__(self):
        return "GameState(move=%d, to_move=%s, winner=%r)" % (
            self.move_count, PLAYER_NAMES.get(self.to_move, self.to_move), self.winner)


class Game:
    """Havannah game logic (sequential, perfect information, no chance)."""

    num_players = NUM_PLAYERS
    num_distinct_actions = N

    # -- lifecycle ---------------------------------------------------------
    def initial_state(self):
        return GameState()

    def current_player(self, state):
        if state.winner is not None:
            return TERMINAL
        return state.to_move

    def is_terminal(self, state):
        return state.winner is not None

    def returns(self, state):
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLACK:
            return [-1.0, 1.0]
        # Draw or not-yet-decided.
        return [0.0, 0.0]

    # -- actions -----------------------------------------------------------
    def legal_actions(self, state):
        if state.winner is not None:
            return []
        if state.stones_left[state.to_move] <= 0:
            return []
        board = state.board
        return [i for i in range(N) if board[i] == EMPTY]

    def apply_action(self, state, action):
        """Place a stone for the current player; return the resulting state."""
        if isinstance(action, str):
            action = self.name_to_action(action)
        if state.winner is not None:
            raise ValueError("game is already over")
        if not isinstance(action, int) or action < 0 or action >= N:
            raise ValueError("action out of range: %r" % (action,))
        if state.board[action] != EMPTY:
            raise ValueError("cell %s is occupied" % self.action_to_name(action))
        p = state.to_move
        if state.stones_left[p] <= 0:
            raise ValueError("player %s has no stones left" % PLAYER_NAMES[p])

        ns = state.copy()
        ns.board[action] = p
        ns.stones_left[p] -= 1
        ns.move_count += 1
        ns.last_move = action

        if self._is_win(ns.board, action, p):
            ns.winner = p
            # to_move is left unchanged; the game is terminal.
        else:
            nxt = 1 - p
            ns.to_move = nxt
            if ns.stones_left[nxt] <= 0 or all(c != EMPTY for c in ns.board):
                ns.winner = DRAW            # neither player can continue, no figure
        return ns

    # -- win detection -----------------------------------------------------
    def _component(self, board, idx, p):
        seen = {idx}
        dq = deque((idx,))
        while dq:
            c = dq.popleft()
            for nb in NEIGHBORS[c]:
                if nb not in seen and board[nb] == p:
                    seen.add(nb)
                    dq.append(nb)
        return seen

    def _has_ring(self, board, comp):
        """True iff the connected group `comp` encloses at least one point.

        Flood-fill every non-group point reachable from the hex outline; any
        non-group point that cannot be reached is enclosed by the group, which
        is exactly the topological condition for a Havannah ring.  The board
        edge never acts as part of a ring, since an outline point that is not
        part of the group is itself an escape to the outside.
        """
        visited = set()
        dq = deque()
        for i in range(N):
            if i not in comp and BOUNDARY[i]:
                if i not in visited:
                    visited.add(i)
                    dq.append(i)
        while dq:
            c = dq.popleft()
            for nb in NEIGHBORS[c]:
                if nb not in comp and nb not in visited:
                    visited.add(nb)
                    dq.append(nb)
        for i in range(N):
            if i not in comp and i not in visited:
                return True
        return False

    def _is_win(self, board, idx, p):
        comp = self._component(board, idx, p)
        # Bridge: group touches at least two corners.
        if sum(1 for c in comp if CORNER[c]) >= 2:
            return True
        # Fork: group touches at least three distinct sides (corners excluded).
        sides = set()
        for c in comp:
            sd = SIDE[c]
            if sd is not None:
                sides.add(sd)
                if len(sides) >= 3:
                    return True
        # Ring: group encloses at least one point.
        return self._has_ring(board, comp)

    # -- action naming -----------------------------------------------------
    def action_to_name(self, action):
        if not isinstance(action, int) or action < 0 or action >= N:
            raise ValueError("action out of range: %r" % (action,))
        q, r = CELLS[action]
        return "place:q%s_r%s" % (_coord_token(q), _coord_token(r))

    def name_to_action(self, name):
        m = _NAME_RE.match(name.strip())
        if not m:
            raise ValueError("unparseable action name: %r" % (name,))
        q = _parse_coord(m.group(1))
        r = _parse_coord(m.group(2))
        idx = CELL_INDEX.get((q, r))
        if idx is None:
            raise ValueError("coordinates off board: q=%d r=%d" % (q, r))
        return idx

    # -- rendering ---------------------------------------------------------
    def render(self, state):
        rows = 2 * R + 1
        cols = 4 * R + 1
        grid = [[" "] * cols for _ in range(rows)]
        for i, (q, r) in enumerate(CELLS):
            grid[r + R][2 * q + r + 2 * R] = PLAYER_CHARS[state.board[i]]
        body = "\n".join("".join(row).rstrip() for row in grid)

        if state.winner == RED:
            status = "result: Red wins"
        elif state.winner == BLACK:
            status = "result: Black wins"
        elif state.winner == DRAW:
            status = "result: draw"
        else:
            status = "to_move: %s" % PLAYER_NAMES[state.to_move]
        last = self.action_to_name(state.last_move) if state.last_move is not None else "-"
        header = "Havannah (side %d, %d points)  move:%d  %s  last:%s  stones[R=%d,B=%d]" % (
            BOARD_SIDE, N, state.move_count, status, last,
            state.stones_left[RED], state.stones_left[BLACK])
        return header + "\n" + body + "\nlegend: R=Red B=Black .=empty"


if __name__ == "__main__":
    g = Game()
    s = g.initial_state()
    assert N == 169 and sum(CORNER) == 6
    print(g.render(s))
    print("legal actions:", len(g.legal_actions(s)))
    print("sample name:", g.action_to_name(g.legal_actions(s)[0]))


```
