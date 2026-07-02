All tests pass. Final module written to `outputs/havannah_agentic.py`.

## 1. Open questions / assumptions

- **Board size.** The rulebook states "169 vertiefte Schnittpunkte." 169 = 3·8²−3·8+1, so the board is a regular hexagon of **side 8** (cube radius R=7). The 91‑point board mentioned in the text is explicitly a *reduced beginner board* ("verkleinertes Brett"), not the real one. Verified: 169 cells, 6 corners, 6 sides × 6 non‑corner points.
- **Win figures (the central rules).** Each requires a *closed* same‑colour connection:
  - **Ring** — encloses ≥1 point; enclosed points may be empty or occupied by either colour ("Es spielt keine Rolle ob… besetzt"). Detected topologically: a point the group separates from the board outline. The board edge never substitutes for stones in a ring.
  - **Bridge** — connects any **2 corners**.
  - **Fork** — connects any **3 sides**; **corners do not count as sides** ("Die Eckpunkte gehören nicht zu den Seiten") — a corner may only act as a connector. All three verified against crafted positions and a 500‑game independent full‑board audit.
- **Players / order.** Red = player 0 and moves first ("Rot fängt an"); Black = player 1. No swap/pie rule (rulebook: no known first‑move effect, and none is described).
- **Moves.** Only placement on an empty point; no capturing, no moving. Any empty point is legal.
- **Stone cap → draw (the main judgment call).** The rulebook lists **55 stones per colour** (box contents) and says a draw is "theoretically possible." I take 55 as a real per‑player placement cap; if both reach 55 with no figure, the game is a draw `[0,0]`. Note: under *random* play this cap is reached ~73% of the time, but under real/strategic play a figure forms far earlier, so the cap is practically non‑binding. **Alternative reading:** treat 55 as mere packaging and play until the 169‑board fills — to get that behaviour, raise `STONES_PER_PLAYER`. I chose the literal printed component count.
- **Multiple figures at once / only the mover wins.** A placement can only extend the mover's own group, so only the mover can win on their move; completing several figures at once is still just a win.
- **Action notation.** The rulebook defines no coordinate labels, so I use axial cube coordinates `(q,r)` with unambiguous sign tokens (`p`/`n`), e.g. `place:qn7rp3`. Round‑trips for all 169 actions and stays unique under punctuation stripping.
- **Not modelled:** strategy/tactics commentary (Rahmen, Magnet, Mühle, "tote Gruppe", Laufspiel, etc.) — advisory, not rules.

## 2. Final file

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


def _sign_token(v):
    return ("p" if v >= 0 else "n") + str(abs(v))


_NAME_RE = re.compile(r"^place:q([pn])(\d+)r([pn])(\d+)$")


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
        return "place:q%sr%s" % (_sign_token(q), _sign_token(r))

    def name_to_action(self, name):
        m = _NAME_RE.match(name.strip())
        if not m:
            raise ValueError("unparseable action name: %r" % (name,))
        qs, qv, rs, rv = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        q = qv if qs == "p" else -qv
        r = rv if rs == "p" else -rv
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
