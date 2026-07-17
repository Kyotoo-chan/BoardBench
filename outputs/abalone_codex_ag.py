"""Small, self-contained implementation of the supplied German Abalone rules."""
from dataclasses import dataclass
from typing import Tuple

Coord = Tuple[int, int]
Action = Tuple[str, Tuple[Coord, ...], int]
DIRECTIONS: Tuple[Coord, ...] = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
DIRECTION_NAMES = ("O", "NO", "NW", "W", "SW", "SO")
AXES = DIRECTIONS[:3]
COLORS = ("Schwarz", "Weiß")


def _inside(c: Coord) -> bool:
    q, r = c
    return max(abs(q), abs(r), abs(q + r)) <= 4


def _add(a: Coord, b: Coord) -> Coord:
    return a[0] + b[0], a[1] + b[1]


@dataclass(frozen=True)
class GameState:
    """Board entries are ``(q, r, colour)``; colour 0 is Schwarz, 1 is Weiß."""

    board: Tuple[Tuple[int, int, int], ...]
    player: int = 0
    ejected: Tuple[int, int] = (0, 0)


class Game:
    """Atomic turns: choose one legal Bewegung, then the other colour plays."""

    @staticmethod
    def initial_state() -> GameState:
        board = []
        # Figure 1: five, six, then the central three on each opposing side.
        for r, qs in ((-4, range(0, 5)), (-3, range(-1, 5)), (-2, range(0, 3))):
            board.extend((q, r, 0) for q in qs)
        for r, qs in ((4, range(-4, 1)), (3, range(-4, 2)), (2, range(-2, 1))):
            board.extend((q, r, 1) for q in qs)
        return GameState(tuple(sorted(board)))

    @staticmethod
    def current_player(state: GameState):
        return None if Game.is_terminal(state) else state.player

    @staticmethod
    def _groups(state: GameState):
        occupied = {(q, r): colour for q, r, colour in state.board}
        own = {c for c, colour in occupied.items() if colour == state.player}
        groups = {(c,) for c in own}
        for c in own:
            for axis in AXES:
                c2 = _add(c, axis)
                if c2 in own:
                    groups.add(tuple(sorted((c, c2))))
                    c3 = _add(c2, axis)
                    if c3 in own:
                        groups.add(tuple(sorted((c, c2, c3))))
        return groups

    @staticmethod
    def legal_actions(state: GameState) -> Tuple[Action, ...]:
        if Game.is_terminal(state):
            return ()
        occupied = {(q, r): colour for q, r, colour in state.board}
        actions = []
        for group in Game._groups(state):
            cells = set(group)
            aligned = set()
            if len(group) > 1:
                delta = (group[1][0] - group[0][0], group[1][1] - group[0][1])
                for i, d in enumerate(DIRECTIONS):
                    if delta[0] * d[1] == delta[1] * d[0]:
                        aligned.add(i)
            for i, direction in enumerate(DIRECTIONS):
                if len(group) == 1 or i in aligned:  # Bewegung in gerader Linie
                    lead = next(c for c in group if _add(c, direction) not in cells)
                    target = _add(lead, direction)
                    if not _inside(target):
                        continue
                    colour = occupied.get(target)
                    if colour is None:
                        actions.append(("move", group, i))
                    elif colour != state.player:
                        count = 0
                        cursor = target
                        while _inside(cursor) and occupied.get(cursor) == colour:
                            count += 1
                            cursor = _add(cursor, direction)
                        if count < len(group) and (not _inside(cursor) or cursor not in occupied):
                            actions.append(("move", group, i))
                else:  # Bewegung zur Seite: every adjacent hollow must be free.
                    targets = [_add(c, direction) for c in group]
                    if all(_inside(c) and c not in occupied for c in targets):
                        actions.append(("move", group, i))
        return tuple(sorted(actions))

    @staticmethod
    def apply_action(state: GameState, action: Action) -> GameState:
        if action not in Game.legal_actions(state):
            raise ValueError("illegal action")
        _, group, direction_index = action
        direction = DIRECTIONS[direction_index]
        board = {(q, r): colour for q, r, colour in state.board}
        cells = set(group)
        inline = len(group) == 1 or any(
            (group[1][0] - group[0][0]) * d[1] == (group[1][1] - group[0][1]) * d[0]
            for d in (direction,)
        )
        expelled = list(state.ejected)
        if inline:
            lead = next(c for c in group if _add(c, direction) not in cells)
            cursor = _add(lead, direction)
            opponents = []
            while _inside(cursor) and board.get(cursor) == 1 - state.player:
                opponents.append(cursor)
                cursor = _add(cursor, direction)
            for c in reversed(opponents):
                colour = board.pop(c)
                destination = _add(c, direction)
                if _inside(destination):
                    board[destination] = colour
                else:
                    expelled[colour] += 1
        for c in group:
            board.pop(c)
        for c in group:
            board[_add(c, direction)] = state.player
        entries = tuple(sorted((q, r, colour) for (q, r), colour in board.items()))
        return GameState(entries, 1 - state.player, tuple(expelled))

    @staticmethod
    def is_terminal(state: GameState) -> bool:
        return state.ejected[0] >= 6 or state.ejected[1] >= 6

    @staticmethod
    def returns(state: GameState) -> Tuple[int, int]:
        if not Game.is_terminal(state):
            return (0, 0)
        return (-1, 1) if state.ejected[0] >= 6 else (1, -1)

    @staticmethod
    def render(state: GameState) -> str:
        board = {(q, r): COLORS[colour][0] for q, r, colour in state.board}
        lines = [f"Am Zug: {COLORS[state.player]} | hinaus: S={state.ejected[0]} W={state.ejected[1]}"]
        for r in range(-4, 5):
            qs = range(max(-4, -r - 4), min(4, -r + 4) + 1)
            lines.append(" " * abs(r) + " ".join(board.get((q, r), ".") for q in qs))
        return "\n".join(lines)

    @staticmethod
    def action_to_name(action: Action) -> str:
        if not (isinstance(action, tuple) and len(action) == 3 and action[0] == "move"):
            raise ValueError("invalid action")
        _, group, i = action
        label = "Bewegung in gerader Linie"
        if len(group) > 1:
            delta = (group[1][0] - group[0][0], group[1][1] - group[0][1])
            d = DIRECTIONS[i]
            if delta[0] * d[1] != delta[1] * d[0]:
                label = "Bewegung zur Seite"
        cells = ";".join(f"{q},{r}" for q, r in group)
        return f"{label}: [{cells}] -> {DIRECTION_NAMES[i]}"

    @staticmethod
    def name_to_action(name: str) -> Action:
        try:
            _, rest = name.split(": [", 1)
            cells_text, direction_name = rest.split("] -> ", 1)
            group = tuple(tuple(map(int, c.split(","))) for c in cells_text.split(";"))
            action = ("move", tuple(sorted(group)), DIRECTION_NAMES.index(direction_name))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid action name") from exc
        if Game.action_to_name(action) != name:
            raise ValueError("invalid or non-canonical action name")
        return action


if __name__ == "__main__":
    game = Game()
    state = game.initial_state()
    actions = game.legal_actions(state)
    assert len(state.board) == 28 and actions
    assert all(game.name_to_action(game.action_to_name(a)) == a for a in actions)
