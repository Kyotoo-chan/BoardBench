from dataclasses import dataclass
from collections import defaultdict, deque
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

TERMINAL = -1
EMPTY = -1
RED = 0
BLUE = 1

PLAYER_NAMES = ("Red", "Blue")
OWNER_CHARS = {EMPTY: ".", RED: "R", BLUE: "B"}

Coord = Tuple[int, int]


@dataclass(frozen=True)
class GameState:
    occupants: Tuple[int, ...]
    to_play: int = RED
    terminal: bool = False
    winner: Optional[int] = None
    terminal_reason: str = ""
    history: Tuple[str, ...] = ()


class Game:
    """Self-contained approximation of Conect from the supplied rule text only."""

    _DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))

    def __init__(self, size: int = 5, center_label: Optional[str] = None):
        if not isinstance(size, int) or size < 3:
            raise ValueError("size must be an integer >= 3")
        if center_label is None and size % 2 == 0:
            raise ValueError("default center needs odd size; provide center_label for even sizes")

        self.size = size
        self.num_players = 2
        self.player_names = PLAYER_NAMES
        self._build_board(center_label)

    def initial_state(self) -> GameState:
        return GameState(occupants=(EMPTY,) * len(self.labels))

    def current_player(self, state: GameState) -> int:
        self._validate_state(state)
        return TERMINAL if state.terminal else state.to_play

    def legal_actions(self, state: GameState) -> List[str]:
        self._validate_state(state)
        if state.terminal:
            return []
        return [
            "place:" + self.labels[i]
            for i, owner in enumerate(state.occupants)
            if owner == EMPTY
        ]

    def apply_action(self, state: GameState, action: str) -> GameState:
        self._validate_state(state)
        if state.terminal:
            raise ValueError("Cannot apply an action to a terminal state")

        name = self.action_to_name(action)
        label = name[len("place:"):]
        index = self.label_to_index[label]
        if state.occupants[index] != EMPTY:
            raise ValueError("Illegal action: target cell is occupied")

        player = state.to_play
        occupants = list(state.occupants)
        occupants[index] = player
        occupants_tuple = tuple(occupants)

        reason = self._winning_reason(occupants_tuple, player)
        if reason:
            return GameState(
                occupants=occupants_tuple,
                to_play=TERMINAL,
                terminal=True,
                winner=player,
                terminal_reason=reason,
                history=state.history + (name,),
            )

        if all(owner != EMPTY for owner in occupants_tuple):
            return GameState(
                occupants=occupants_tuple,
                to_play=TERMINAL,
                terminal=True,
                winner=None,
                terminal_reason="draw:board_full",
                history=state.history + (name,),
            )

        return GameState(
            occupants=occupants_tuple,
            to_play=BLUE if player == RED else RED,
            terminal=False,
            winner=None,
            terminal_reason="",
            history=state.history + (name,),
        )

    def is_terminal(self, state: GameState) -> bool:
        self._validate_state(state)
        return state.terminal

    def returns(self, state: GameState) -> List[float]:
        self._validate_state(state)
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLUE:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def render(self, state: GameState) -> str:
        self._validate_state(state)
        turn = "terminal" if state.terminal else PLAYER_NAMES[state.to_play]
        if state.terminal:
            winner = "draw" if state.winner is None else PLAYER_NAMES[state.winner]
        else:
            winner = "none"

        lines = [
            f"turn={turn}",
            f"winner={winner}",
            f"reason={state.terminal_reason or '-'}",
            f"size={self.size}",
            f"center={self.labels[self.center_index]}",
            "red_edge=" + ",".join(self.labels[i] for i in self.edge_sequences[RED]),
            "blue_edge=" + ",".join(self.labels[i] for i in self.edge_sequences[BLUE]),
            "rows:",
        ]

        for r, row in enumerate(self.render_rows):
            entries = [f"{self.labels[i]}:{OWNER_CHARS[state.occupants[i]]}" for i in row]
            lines.append(f"r{r} " + " ".join(entries))

        lines.append("history=" + ",".join(state.history))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are canonical strings such as 'place:q2r2'")
        if not action.startswith("place:"):
            raise ValueError("unknown action format")
        label = action[len("place:"):]
        if label not in self.label_to_index:
            raise ValueError("unknown cell label")
        return "place:" + label

    def name_to_action(self, name: str) -> str:
        return self.action_to_name(name)

    # Board construction assumptions:
    # - Start from a size x size hex-rhombus with axial-like q/r coordinates.
    # - Identify the adjacent q=0 and r=0 edges to approximate rolling into a cone.
    # - The two unjoined edges are the Red and Blue edge arcs; endpoints are shared.
    def _build_board(self, center_label: Optional[str]) -> None:
        can_to_raws: Dict[Coord, Set[Coord]] = defaultdict(set)

        for q in range(self.size):
            for r in range(self.size):
                can = self._canonical_coord((q, r))
                can_to_raws[can].add((q, r))

        self.coords = tuple(sorted(can_to_raws.keys(), key=self._coord_sort_key))
        self.coord_to_index = {coord: i for i, coord in enumerate(self.coords)}
        self.labels = tuple(self._coord_to_label(coord) for coord in self.coords)
        if len(set(self.labels)) != len(self.labels):
            raise RuntimeError("internal cell label collision")
        self.label_to_index = {label: i for i, label in enumerate(self.labels)}

        adj_by_coord: Dict[Coord, Set[Coord]] = {coord: set() for coord in self.coords}
        for coord, raws in can_to_raws.items():
            for q, r in raws:
                for dq, dr in self._DIRECTIONS:
                    nq, nr = q + dq, r + dr
                    if 0 <= nq < self.size and 0 <= nr < self.size:
                        ncan = self._canonical_coord((nq, nr))
                        if ncan != coord:
                            adj_by_coord[coord].add(ncan)

        self.adjacent = tuple(
            frozenset(self.coord_to_index[ncoord] for ncoord in adj_by_coord[coord])
            for coord in self.coords
        )

        red_seq = tuple(
            self.coord_to_index[self._canonical_coord((self.size - 1, k))]
            for k in range(self.size)
        )
        blue_seq = tuple(
            self.coord_to_index[self._canonical_coord((k, self.size - 1))]
            for k in range(self.size)
        )
        self.edge_sequences = (red_seq, blue_seq)
        self.edge_sets = (frozenset(red_seq), frozenset(blue_seq))
        self.boundary_indices = frozenset(set(red_seq) | set(blue_seq))

        if center_label is None:
            center_coord = self._canonical_coord((self.size // 2, self.size // 2))
            self.center_index = self.coord_to_index[center_coord]
        else:
            if center_label not in self.label_to_index:
                raise ValueError("unknown center_label")
            self.center_index = self.label_to_index[center_label]

        rows = []
        for r in range(self.size):
            row = []
            start_q = 0 if r == 0 else 1  # q=0 cells for r>0 are seam duplicates.
            for q in range(start_q, self.size):
                idx = self.coord_to_index[self._canonical_coord((q, r))]
                if idx not in row:
                    row.append(idx)
            rows.append(tuple(row))
        self.render_rows = tuple(rows)

    def _canonical_coord(self, coord: Coord) -> Coord:
        q, r = coord
        if q == 0 and r > 0:
            return (r, 0)
        return coord

    def _coord_sort_key(self, coord: Coord) -> Tuple[int, int]:
        q, r = coord
        return (r, q)

    def _coord_to_label(self, coord: Coord) -> str:
        q, r = coord
        n = self.size
        if coord == (0, 0):
            return "apex"
        if coord == (n - 1, 0):
            return "shared0"
        if coord == (n - 1, n - 1):
            return "shared1"
        if r == 0:
            return f"seam{q}"
        return f"q{q}r{r}"

    def _validate_state(self, state: GameState) -> None:
        if not isinstance(state, GameState):
            raise TypeError("state must be a GameState")
        if not isinstance(state.occupants, tuple) or len(state.occupants) != len(self.labels):
            raise ValueError("state has wrong occupant vector size")
        for owner in state.occupants:
            if owner not in (EMPTY, RED, BLUE):
                raise ValueError("state contains an invalid occupant")
        if not isinstance(state.terminal, bool):
            raise ValueError("state terminal flag must be bool")
        if state.terminal:
            if state.winner not in (None, RED, BLUE):
                raise ValueError("invalid winner")
            if state.to_play not in (TERMINAL, RED, BLUE):
                raise ValueError("invalid to_play")
        else:
            if state.to_play not in (RED, BLUE):
                raise ValueError("invalid player to move")
            if state.winner is not None:
                raise ValueError("non-terminal state cannot already have a winner")

    def _winning_reason(self, occupants: Tuple[int, ...], player: int) -> str:
        components = self._player_components(occupants, player)

        if self._edge_loop_win(components, player):
            return "win:edge_loop"
        if self._surround_group_win(components, player):
            return "win:surround_group"
        if self._center_path_win(occupants, components, player):
            return "win:center_path"
        return ""

    def _player_components(
        self, occupants: Tuple[int, ...], player: int
    ) -> List[FrozenSet[int]]:
        seen: Set[int] = set()
        components: List[FrozenSet[int]] = []

        for start, owner in enumerate(occupants):
            if owner != player or start in seen:
                continue
            comp: Set[int] = set()
            queue = deque([start])
            seen.add(start)

            while queue:
                cell = queue.popleft()
                comp.add(cell)
                for nb in self.adjacent[cell]:
                    if nb not in seen and occupants[nb] == player:
                        seen.add(nb)
                        queue.append(nb)

            components.append(frozenset(comp))

        return components

    def _center_path_win(
        self,
        occupants: Tuple[int, ...],
        components: List[FrozenSet[int]],
        player: int,
    ) -> bool:
        if occupants[self.center_index] != player:
            return False
        for comp in components:
            if self.center_index in comp:
                return bool(comp & self.edge_sets[player])
        return False

    def _surround_group_win(self, components: List[FrozenSet[int]], player: int) -> bool:
        for comp in components:
            if self.center_index in comp:
                continue
            if not (comp & self.edge_sets[player]):
                continue
            if not self._center_can_reach_boundary(comp):
                return True
        return False

    def _edge_loop_win(self, components: List[FrozenSet[int]], player: int) -> bool:
        # Assumption for rule 1: the colored edge segment between two endpoint
        # stones closes the loop even if those intermediary edge cells are empty.
        seq = self.edge_sequences[player]

        for comp in components:
            if self.center_index in comp:
                continue

            touched_positions = [pos for pos, idx in enumerate(seq) if idx in comp]
            if len(touched_positions) < 2:
                continue

            for i, a in enumerate(touched_positions):
                for b in touched_positions[i + 1:]:
                    segment = set(seq[a:b + 1])
                    blocked = set(comp) | segment
                    if self.center_index in blocked:
                        continue
                    if not self._center_can_reach_boundary(blocked):
                        return True

        return False

    def _center_can_reach_boundary(self, blocked: Iterable[int]) -> bool:
        blocked_set = set(blocked)
        if self.center_index in blocked_set:
            return False

        seen = {self.center_index}
        queue = deque([self.center_index])

        while queue:
            cell = queue.popleft()
            if cell in self.boundary_indices:
                return True
            for nb in self.adjacent[cell]:
                if nb not in blocked_set and nb not in seen:
                    seen.add(nb)
                    queue.append(nb)

        return False
