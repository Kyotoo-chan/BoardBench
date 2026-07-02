**Open questions / assumptions**

- The board is modeled as the 169-point hexagonal triangular lattice implied by the rulebook image and point count: side length 8.
- Player 0 is red and starts; player 1 is black. The pre-game color lottery is not modeled.
- Each player has 55 stones, matching the listed contents. If no one wins before the next player has no stones, the game is a draw.
- The optional 91-point beginner board from the strategy text is not implemented.
- Ring detection uses the geometric meaning “surrounds at least one point”; strategy-only terms like frames, magnets, traps, etc. are not implemented as rules.

```python
from collections import deque
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


TERMINAL = -1

BOARD_RADIUS = 7          # Hex radius 7 gives 169 points, side length 8.
STONES_PER_PLAYER = 55
PLAYER_NAMES = ("red", "black")

Point = Tuple[int, int]
Action = Tuple[int, int]
BoardEntry = Tuple[int, int, int]

DIRECTIONS: Tuple[Point, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass(frozen=True)
class GameState:
    board: Tuple[BoardEntry, ...] = ()
    player: int = 0
    moves_made: Tuple[int, int] = (0, 0)
    winner: Optional[int] = None
    winning_kind: Optional[str] = None
    history: Tuple[str, ...] = ()


class Game:
    def __init__(self):
        self.num_players = 2
        self.radius = BOARD_RADIUS
        self.points = self._make_points(self.radius)
        self.point_set = set(self.points)
        self.neighbors = {
            point: tuple(
                neighbor
                for neighbor in self._raw_neighbors(point)
                if neighbor in self.point_set
            )
            for point in self.points
        }

        r = self.radius
        self.corners: FrozenSet[Point] = frozenset(
            ((r, -r), (r, 0), (0, r), (-r, r), (-r, 0), (0, -r))
        )
        self.boundary_points = frozenset(
            point for point in self.points if self._is_boundary(point)
        )
        self.sides_by_point = {
            point: self._side_membership(point) for point in self.points
        }

        (
            self.faces,
            self.face_edges,
            self.edge_faces,
            self.point_faces,
        ) = self._build_faces()

    def initial_state(self):
        return GameState()

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        return state.player

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        if state.player not in (0, 1):
            return []
        if state.moves_made[state.player] >= STONES_PER_PLAYER:
            return []

        occupied = set(self._board_map(state))
        return [point for point in self.points if point not in occupied]

    def apply_action(self, state, action):
        action = self._normalize_action(action)
        legal = set(self.legal_actions(state))
        if action not in legal:
            raise ValueError("illegal action: {}".format(action))

        board = self._board_map(state)
        board[action] = state.player

        moves = list(state.moves_made)
        moves[state.player] += 1

        winning_kinds = self._winning_kinds(board, state.player)
        winner = state.player if winning_kinds else None
        winning_kind = "+".join(winning_kinds) if winning_kinds else None

        return GameState(
            board=self._board_tuple(board),
            player=1 - state.player,
            moves_made=tuple(moves),
            winner=winner,
            winning_kind=winning_kind,
            history=state.history + (self.action_to_name(action),),
        )

    def is_terminal(self, state):
        if state.winner is not None:
            return True
        if len(state.board) >= len(self.points):
            return True
        if state.player in (0, 1):
            return state.moves_made[state.player] >= STONES_PER_PLAYER
        return False

    def returns(self, state):
        if state.winner is None:
            return [0.0, 0.0]
        return [
            1.0 if player == state.winner else -1.0
            for player in range(self.num_players)
        ]

    def render(self, state):
        board = self._board_map(state)
        lines = []

        if state.winner is not None:
            lines.append(
                "status=terminal winner={} via={}".format(
                    PLAYER_NAMES[state.winner], state.winning_kind
                )
            )
        elif self.is_terminal(state):
            lines.append("status=terminal winner=none")
        else:
            lines.append("status=active to_move={}".format(PLAYER_NAMES[state.player]))

        lines.append(
            "stones=red:{}/{} black:{}/{}".format(
                state.moves_made[0],
                STONES_PER_PLAYER,
                state.moves_made[1],
                STONES_PER_PLAYER,
            )
        )
        lines.append("rows=q_increasing")

        for row in range(-self.radius, self.radius + 1):
            row_points = [point for point in self.points if point[1] == row]
            cells = []
            for point in row_points:
                owner = board.get(point)
                if owner is None:
                    cells.append(".")
                elif owner == 0:
                    cells.append("R")
                elif owner == 1:
                    cells.append("B")
                else:
                    cells.append("?")
            lines.append(
                "r_{} {}{}".format(
                    self._coord_token(row),
                    " " * abs(row),
                    " ".join(cells),
                )
            )

        return "\n".join(lines)

    def action_to_name(self, action):
        q, r = self._normalize_action(action)
        if (q, r) not in self.point_set:
            raise ValueError("action point is not on the board")
        return "place:q_{}:r_{}".format(self._coord_token(q), self._coord_token(r))

    def name_to_action(self, name):
        parts = name.split(":")
        if len(parts) != 3 or parts[0] != "place":
            raise ValueError("invalid action name: {}".format(name))

        q = self._parse_named_coord(parts[1], "q")
        r = self._parse_named_coord(parts[2], "r")
        action = (q, r)
        if action not in self.point_set:
            raise ValueError("named point is not on the board")
        if self.action_to_name(action) != name:
            raise ValueError("non-canonical action name: {}".format(name))
        return action

    def _winning_kinds(self, board, player):
        kinds = []
        components = self._player_components(board, player)

        if self._has_ring(board, player):
            kinds.append("ring")

        if any(len(component & self.corners) >= 2 for component in components):
            kinds.append("bridge")

        for component in components:
            touched_sides = set()
            for point in component:
                touched_sides.update(self.sides_by_point[point])
            if len(touched_sides) >= 3:
                kinds.append("fork")
                break

        return tuple(kinds)

    def _has_ring(self, board, player):
        # Faces are separated by stone-to-stone edges of the tested player.
        # A ring exists when at least one non-boundary board point has no
        # adjacent triangular face reachable from outside the board.
        outside_reachable = set()
        queue = deque()

        def add_face(face_id):
            if face_id not in outside_reachable:
                outside_reachable.add(face_id)
                queue.append(face_id)

        for edge, face_ids in self.edge_faces.items():
            if len(face_ids) == 1 and not self._edge_blocked(edge, board, player):
                add_face(face_ids[0])

        while queue:
            face_id = queue.popleft()
            for edge in self.face_edges[face_id]:
                if self._edge_blocked(edge, board, player):
                    continue
                for next_face in self.edge_faces[edge]:
                    if next_face != face_id:
                        add_face(next_face)

        for point in self.points:
            if point in self.boundary_points:
                continue
            incident = self.point_faces[point]
            if incident and all(face_id not in outside_reachable for face_id in incident):
                return True

        return False

    def _edge_blocked(self, edge, board, player):
        a, b = edge
        return board.get(a) == player and board.get(b) == player

    def _player_components(self, board, player):
        stones = {point for point, owner in board.items() if owner == player}
        seen = set()
        components = []

        for start in sorted(stones, key=self._sort_key):
            if start in seen:
                continue
            component = set()
            stack = [start]
            seen.add(start)

            while stack:
                point = stack.pop()
                component.add(point)
                for neighbor in self.neighbors[point]:
                    if neighbor in stones and neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)

            components.append(component)

        return components

    def _build_faces(self):
        face_set = set()

        for point in self.points:
            q, r = point
            for index, first in enumerate(DIRECTIONS):
                second = DIRECTIONS[(index + 1) % len(DIRECTIONS)]
                a = (q + first[0], r + first[1])
                b = (q + second[0], r + second[1])
                if a in self.point_set and b in self.point_set:
                    face_set.add(tuple(sorted((point, a, b), key=self._sort_key)))

        faces = tuple(
            sorted(face_set, key=lambda face: tuple(self._sort_key(p) for p in face))
        )

        edge_faces_lists: Dict[Tuple[Point, Point], List[int]] = {}
        point_faces_lists: Dict[Point, List[int]] = {point: [] for point in self.points}
        face_edges = []

        for face_id, face in enumerate(faces):
            edges = (
                self._edge_key(face[0], face[1]),
                self._edge_key(face[1], face[2]),
                self._edge_key(face[2], face[0]),
            )
            face_edges.append(edges)

            for edge in edges:
                edge_faces_lists.setdefault(edge, []).append(face_id)
            for point in face:
                point_faces_lists[point].append(face_id)

        edge_faces = {
            edge: tuple(face_ids) for edge, face_ids in edge_faces_lists.items()
        }
        point_faces = {
            point: tuple(face_ids) for point, face_ids in point_faces_lists.items()
        }

        return faces, tuple(face_edges), edge_faces, point_faces

    def _side_membership(self, point):
        if point in self.corners:
            return frozenset()

        q, r = point
        s = -q - r
        labels = []

        if q == self.radius:
            labels.append("q_pos")
        if q == -self.radius:
            labels.append("q_neg")
        if r == self.radius:
            labels.append("r_pos")
        if r == -self.radius:
            labels.append("r_neg")
        if s == self.radius:
            labels.append("s_pos")
        if s == -self.radius:
            labels.append("s_neg")

        return frozenset(labels)

    def _is_boundary(self, point):
        q, r = point
        s = -q - r
        return max(abs(q), abs(r), abs(s)) == self.radius

    def _raw_neighbors(self, point):
        q, r = point
        return [(q + dq, r + dr) for dq, dr in DIRECTIONS]

    def _edge_key(self, a, b):
        return tuple(sorted((a, b), key=self._sort_key))

    def _board_map(self, state):
        return {(q, r): owner for q, r, owner in state.board}

    def _board_tuple(self, board):
        return tuple(
            sorted(
                ((q, r, owner) for (q, r), owner in board.items()),
                key=lambda entry: (entry[1], entry[0], entry[2]),
            )
        )

    def _normalize_action(self, action):
        if not isinstance(action, tuple) or len(action) != 2:
            raise ValueError("actions must be (q, r) tuples")
        q, r = action
        if not isinstance(q, int) or not isinstance(r, int):
            raise ValueError("action coordinates must be integers")
        return q, r

    def _parse_named_coord(self, text, axis):
        prefix = axis + "_"
        if not text.startswith(prefix):
            raise ValueError("invalid coordinate field: {}".format(text))

        token = text[len(prefix):]
        if token == "z0":
            return 0
        if len(token) < 2:
            raise ValueError("invalid coordinate token: {}".format(token))

        sign = token[0]
        digits = token[1:]
        if sign not in ("p", "n") or not digits.isdigit():
            raise ValueError("invalid coordinate token: {}".format(token))

        value = int(digits)
        if value == 0:
            raise ValueError("zero must be encoded as z0")
        return value if sign == "p" else -value

    @staticmethod
    def _coord_token(value):
        if value > 0:
            return "p{}".format(value)
        if value < 0:
            return "n{}".format(-value)
        return "z0"

    @staticmethod
    def _sort_key(point):
        q, r = point
        return r, q

    @staticmethod
    def _make_points(radius):
        points = []
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if max(abs(q), abs(r), abs(s)) <= radius:
                    points.append((q, r))
        return tuple(sorted(points, key=lambda point: (point[1], point[0])))
```