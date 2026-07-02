## Open questions / assumptions

- **Starting position (Abb. 1 not provided):** I assume the standard/classic Abalone opening — each player has 14 balls: two full back rows plus the centre three of the third row. This is the single most uncertain point; it is isolated in `initial_state` and easy to change.
- **Board geometry:** Inferred from "sechs Richtungen" + "Mulde": the standard hexagonal Abalone board, side 5, 61 cells, row sizes `5,6,7,8,9,8,7,6,5`, six directions (`E,W,NE,NW,SE,SW`). The rulebook implies but does not draw this.
- **Cell labels:** The rulebook defines no labels (it relies on figures). I use my own stable scheme: rows `A` (bottom) … `I` (top); within a row positions `1..n` left-to-right; centre = `E5`. This may not match any "official" Abalone notation, but it is unique/round-trippable.
- **Colours / turn order:** player `0` = Black (starts — "Schwarz fängt immer an"), player `1` = White. Orientation is arbitrary (Black rendered on top).
- **Win:** push 6 opponent balls off the board (`off >= 6`). Returns `+1 / -1`, draw `0 / 0`.
- **Sumito / Patt:** Pushing only via an **in-line** move, only with a **strict majority** in that line (`attackers > defenders`), and only if the cell behind the defenders is free **or off-board** (off-board = pushed out). This yields exactly the 2-1, 3-1, 3-2 cases. Patt (1-1/2-2/3-3) and the "4-vs-3 counts as 3-3" note need no extra code: you can move at most 3 balls and equal counts cannot push, so they simply produce no push action. The "attack on another line" advice is strategic, not a rule.
- **Broadside moves never push**; all their destinations must be empty and on-board.
- **No pass.** If a player ever has no legal move, the state is terminal; the rulebook does not define the result, so I score it as a draw (documented).
- **Finiteness safeguard:** a hard ply cap (`MAX_PLIES`) ends the game as a draw. This is *not* an Abalone rule (real play uses a clock — "Gegen die Zeit", which I do not model); it only prevents non-terminating automated rollouts.
- Perfect information, deterministic, no chance → `chance_outcomes` / `information_state` omitted.

```python
"""Abalone (Schmidt Spiele edition) — single-file, standard-library implementation.

Cell labels: rows A (bottom) .. I (top); within a row positions 1..n left to right.
Centre cell = E5. (The rulebook defines no labels; this scheme is our own.)

Action name format:  "<cell>[-<cell>[-<cell>]]:<DIR>"  with DIR in E,W,NE,NW,SE,SW
  e.g.  "E5:NE"  (single ball)   "E4-E5:E"  (in-line pair)   "C3-D4-E5:SW" (triple)
A move shifts the named 1..3 own balls one cell in DIR; whether it slides, pushes
(Sumito) or moves broadside is determined by the board, not encoded in the name.
"""

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
    row, col = cell
    return "%s%d" % (chr(ord('A') + row), col + 1)


def label_to_cell(label):
    row = ord(label[0]) - ord('A')
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

    # -- naming (round-trips exactly) --
    def action_to_name(self, action):
        cells, d = action
        return "%s:%s" % ("-".join(cell_to_label(c) for c in cells), d)

    def name_to_action(self, name):
        labels_part, d = name.rsplit(":", 1)
        cells = tuple(sorted(label_to_cell(lbl) for lbl in labels_part.split("-")))
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
