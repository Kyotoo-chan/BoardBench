# BoardBench judge packet

- game: havannah

- OpenSpiel reference: havannah(board_size=8)

- variant: oneshot

- generated code: D:/safen/Ben_T/Studium/8.Semester/BoardBench/outputs/havannah_oneshot.py

- expected judge reply path: D:/safen/Ben_T/Studium/8.Semester/BoardBench/outputs/havannah_oneshot_judge.md



## Judge prompt

# LLM judge scoring prompt

Use this as a qualitative scoring step after a game implementation has been generated. The judge is not the source of truth and must not rewrite the implementation. Its job is to score how well the generated BoardBench environment appears to implement the provided rulebook.

## Inputs to use

Use only the artifacts provided in the packet:

1. the original rulebook text, or the attached/rendered rulebook page images
2. the implementation brief, if one was created
3. the generation prompt/backbones used
4. the generated Python file

Do **not** use outside game knowledge, remembered rules, internet knowledge, or OpenSpiel knowledge unless that material is explicitly included in the packet. If something is not clear from the rulebook, mark it as uncertain rather than wrong.

Do not rerun deterministic checks and do not judge mainly by check logs. The deterministic BoardBench checks are separate. This review should focus on rule fidelity, game logic, assumptions, and testability.

## Scoring target

Give one overall score from `0.0` to `1.0`:

- `1.0`: faithful, complete, and benchmark-ready based on the provided rulebook
- `0.8`: mostly correct with only minor issues or harmless assumptions
- `0.6`: playable but with notable uncertain or partially implemented rule areas
- `0.4`: major rule or state-transition issues likely affect gameplay
- `0.2`: severe missing mechanics or unreliable terminal/scoring logic
- `0.0`: unusable or largely unrelated to the rulebook

Use the full range when justified. Do not give a high score only because the API exists or the code looks clean.

## Review focus

Prioritize:

- setup and board/components
- player count and turn order
- legal actions
- state transitions
- terminal/win/loss/draw conditions
- scoring/returns
- chance handling, if any
- hidden information, if any
- simultaneous moves, if any
- action names/rendering as a BoardBench interface
- unsupported assumptions or invented rules
- likely missing deterministic scenario tests

## Required output format

### 1. Score

Give:

- `score: <number from 0.0 to 1.0>`
- `confidence: low|medium|high`
- a short 2-4 sentence justification

### 2. Top findings

List the most important findings first. For each finding include:

- severity: critical / major / minor / question
- evidence from the rulebook, generated code, or provided artifacts
- why it matters for gameplay or benchmarking
- suggested next action

### 3. Rule coverage review

Create a table with columns:

- rule area
- covered correctly / partially covered / missing / unclear
- evidence
- notes

Cover at least: setup, player count and turn order, legal actions, state transitions, terminal conditions, scoring/returns, rendering/action names, chance/hidden/simultaneous if relevant.

### 4. Unsupported assumptions or invented rules

List every place where the implementation appears to decide something not specified by the provided rulebook. Distinguish harmless conventions from risky invented rules.

### 5. Missing scenario tests

Suggest concrete additional deterministic tests. Prefer action-name sequences that could later be turned into checks.

### 6. Open questions for the human

Ask only questions that materially affect implementation correctness or benchmark scoring.

### 7. Machine-readable summary

End with exactly this compact YAML-like block:

```text
score: <0.0-1.0>
confidence: low|medium|high
critical_issues: <number>
major_issues: <number>
minor_issues: <number>
needs_rulebook_clarification: true|false
needs_code_change: true|false
needs_more_tests: true|false
```




## Generation prompt (prompts/rulebook_to_python.txt)

You will receive rule text.

Use only that information.
Do not use outside knowledge or remembered rules for the game.
If an implementation brief or backbone context is provided, use it only as an interpretation aid; the rule text wins if there is a conflict.

Write one simple, self-contained Python file using only the standard library.
Do not import any non-standard-library package or external game framework.
Do not require external files, images, environment variables, network access, subprocesses, API keys, or interactive input.
Keep top-level code limited to definitions and constants.

If rules are unclear or incomplete, state the assumptions briefly before the code and in comments where relevant.
Do not silently fill missing rules with outside knowledge.
Prefer a smaller explicit implementation with documented gaps over broad invented mechanics.

If possible, include this minimal game API:
- `GameState`
- `Game`
- `initial_state(self)`
- `current_player(self, state)`
- `legal_actions(self, state)`
- `apply_action(self, state, action)` returning the next state, or clearly documenting in-place mutation
- `is_terminal(self, state)`
- `returns(self, state)` returning one numeric value per player
- `render(self, state)` returning a stable, compact, human-readable string suitable for side-by-side inspection
- `action_to_name(self, action)` returning a unique canonical action name
- `name_to_action(self, name)` reversing a canonical action name

Rules for actions and state presentation:
- `legal_actions` must only return actions that `apply_action` accepts.
- `action_to_name` and `name_to_action` must round-trip exactly.
- Action names must be human-readable, stable, unique in sampled states, and must not rely on raw internal indices alone.
- If action names contain signed numeric coordinates, encode signs unambiguously (for example `pos1`/`neg1` or `p1`/`n1`) so different points cannot collapse when punctuation is normalized.
- If the rule text defines labels for squares, points, regions, cards, or other move targets, use those labels in action names and render output.
- If the rule text explicitly defines or clearly implies a standard move notation, use that notation consistently; otherwise use a simple explicit format such as `place:<target>`, `move:<source>-><target>`, `remove:<target>`, or similarly clear equivalents.
- `render` should be deterministic across repeated calls on the same state and avoid decorative prose.
- Terminal states should have no legal actions and stable returns.

Only if required by the rule text, include:
- `chance_outcomes(self, state)` for stochastic rules
- `information_state(self, state, player)` for hidden-information rules

Output:
1. `Open questions / assumptions`
2. one fenced `python` code block with the full file




## OpenSpiel backbone (prompts/open_spiel_backbone.md)

# OpenSpiel-inspired BoardBench backbone

Use this as extra context with `prompts/rulebook_to_python.txt` and the rulebook.

This is an interface/backbone, not a dependency. Generated code must stay one self-contained standard-library Python file. Do not import `pyspiel`, `open_spiel`, external frameworks, files, network, subprocesses, or API keys.

Use OpenSpiel only for structure: explicit state, legal actions, deterministic transitions, optional chance nodes, optional information states, stable action names, and numeric returns. The rulebook is always the source of truth.

## Required shape

Implement:

```python
class GameState:
    ...

class Game:
    def initial_state(self): ...
    def current_player(self, state): ...
    def legal_actions(self, state): ...
    def apply_action(self, state, action): ...
    def is_terminal(self, state): ...
    def returns(self, state): ...
    def render(self, state): ...
    def action_to_name(self, action): ...
    def name_to_action(self, name): ...
```

Optional only if the rulebook needs them:

```python
def chance_outcomes(self, state): ...        # [(action, probability), ...]
def information_state(self, state, player): ...
def observation(self, state, player): ...
def rewards(self, state): ...               # latest step rewards if separate from returns
```

Suggested sentinel constants:

```python
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3
```

`current_player(state)` should return a player index, `TERMINAL`, `CHANCE`, or `SIMULTANEOUS`.

## Implementation recipe

1. Classify the game from the rulebook: player count, turn structure, chance, hidden information, scoring type.
2. Define `GameState` fields first: public state, private state, phase, current player, scores/returns, history.
3. Define action objects and canonical action names before transition logic.
4. Implement `legal_actions` as a pure deterministic function of state.
5. Implement `apply_action` by validating the action, updating state, switching player/phase, and updating terminal/returns.
6. Keep scoring and terminal rules separate enough to inspect and test.
7. Make `render` compact, deterministic, and useful for side-by-side comparison.
8. Document assumptions exactly where the rulebook is unclear.

Prefer returning a fresh state from `apply_action`. If mutating in place, document it clearly.

## Invariants

- `initial_state()` returns a fresh state.
- terminal states have no legal actions.
- non-terminal player states have legal actions unless the rulebook explicitly allows a dead state.
- `legal_actions` lists only actions accepted by `apply_action`.
- `returns` always has one numeric value per player.
- `render` is deterministic for the same state.
- `action_to_name` and `name_to_action` round-trip for legal actions.
- chance probabilities, if present, are non-negative and sum to 1.
- hidden-information views, if present, do not reveal private data to the wrong player.
- max length / repetition / pass rules are encoded when needed to avoid accidental infinite games.

## Action names

Use rulebook labels whenever available. Otherwise use explicit names:

- `place:<target>`
- `move:<source>-><target>`
- `remove:<target>`
- `claim:<item>`
- `bid:<amount>`
- `pass`
- `chance:deal:<card>`
- `chance:roll:<value>`
- `p0:<a0>|p1:<a1>` for simultaneous joint actions

Avoid names that only expose internal indices unless the rulebook itself uses those indices.

## Game-type add-ons

### Sequential perfect-information games

Use when exactly one player acts and all relevant state is public.

- no `chance_outcomes` or `information_state` needed
- switch the current player after each normal action unless the rules say otherwise
- test wins/draws, blocked/illegal moves, and terminal no-actions behavior

### Chance/stochastic games

Use when cards, dice, random setup, or random events affect play.

- model randomness as explicit chance actions, never hidden calls to `random`
- `current_player` returns `CHANCE` at chance nodes
- `chance_outcomes(state)` returns probabilities for the same chance actions that `legal_actions(state)` returns without probabilities
- `apply_action` consumes the selected chance action deterministically

### Hidden-information games

Use when hands, cards, objectives, or other facts are private.

- keep full truth in `GameState` for correctness
- expose player-visible data through `information_state(state, player)`
- `render(state)` may be full debug state, but document that it is not player-visible
- action names must not leak hidden data unless the action legally reveals it

### Simultaneous-move games

Use when players commit actions before seeing others' choices.

```python
def legal_actions(self, state, player=None): ...
def legal_joint_actions(self, state): ...
def apply_actions(self, state, actions_by_player): ...
```

For simple BoardBench rollouts, `legal_actions(state)` at a simultaneous node should return joint actions that `apply_action(state, joint_action)` can resolve. Name joint actions as `p0:<a0>|p1:<a1>`.

### Multiplayer, teams, or general-sum scoring

- set `num_players` from the rulebook
- `returns(state)` length must equal `num_players`
- map team scores to each individual player explicitly
- handle skipped/eliminated players in turn order

### Repeated rounds or step rewards

- keep cumulative returns separate from latest `rewards(state)` if step rewards matter
- reset round-local state without losing cumulative scores
- encode round limits, target score, or other stop rules

### Games with OpenSpiel references

If comparing against OpenSpiel later:

- prefer rulebook-compatible action names that canonicalize well against OpenSpiel action strings
- keep `render` compact enough for side-by-side inspection
- document deliberate mismatches caused by incomplete rulebook text




## Rulebook PDF (inputs/game_rules.pdf)

The PDF has no extractable text. Use these rendered page images as the rulebook source:

![page-1.png](inputs/rulebook_pages/game_rules/page-1.png)

![page-2.png](inputs/rulebook_pages/game_rules/page-2.png)

![page-3.png](inputs/rulebook_pages/game_rules/page-3.png)



## Generated code (D:/safen/Ben_T/Studium/8.Semester/BoardBench/outputs/havannah_oneshot.py)

```python
from dataclasses import dataclass
import math

TERMINAL = -1

EMPTY = -1
RED = 0
BLACK = 1

PLAYER_NAMES = ("Red", "Black")
SYMBOLS = {EMPTY: ".", RED: "R", BLACK: "B"}

SIDE_LENGTH = 8
RADIUS = SIDE_LENGTH - 1
STONES_PER_PLAYER = 55

# Axial-neighbor directions on the triangular/hexagonal point grid.
DIRECTIONS = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


def _sign_label(value):
    if value > 0:
        return "p" + str(value)
    if value < 0:
        return "n" + str(-value)
    return "z0"


def _action_sign_label(value):
    # Action names use the BoardBench-normalizer-friendly canonical spelling:
    # pN / nN for signed coordinates and plain 0 for zero.
    if value > 0:
        return "p" + str(value)
    if value < 0:
        return "n" + str(-value)
    return "0"


def _parse_action_sign_label(text):
    if text == "0":
        return 0
    if len(text) < 2:
        raise ValueError("bad signed coordinate")
    sign = text[0]
    digits = text[1:]
    if sign not in ("p", "n") or not digits.isdigit():
        raise ValueError("bad signed coordinate")
    if len(digits) > 1 and digits[0] == "0":
        raise ValueError("non-canonical leading zero")
    value = int(digits)
    if value <= 0:
        raise ValueError("p/n coordinates must be nonzero")
    return value if sign == "p" else -value


def _parse_signed_label(text):
    if len(text) < 2:
        raise ValueError("bad signed coordinate")
    sign = text[0]
    digits = text[1:]
    if sign not in ("p", "n", "z") or not digits.isdigit():
        raise ValueError("bad signed coordinate")
    if sign == "z":
        if digits != "0":
            raise ValueError("zero must be encoded as z0")
        return 0
    if len(digits) > 1 and digits[0] == "0":
        raise ValueError("non-canonical leading zero")
    value = int(digits)
    if value <= 0:
        raise ValueError("p/n coordinates must be nonzero")
    return value if sign == "p" else -value


def _q_range_for_r(r):
    return max(-RADIUS, -r - RADIUS), min(RADIUS, -r + RADIUS)


def _build_points():
    points = []
    for r in range(-RADIUS, RADIUS + 1):
        q_min, q_max = _q_range_for_r(r)
        for q in range(q_min, q_max + 1):
            points.append((q, r))
    return tuple(points)


def _cube(point):
    q, r = point
    return q, r, -q - r


def _xy(point):
    q, r = point
    # Affine integer embedding of the axial grid.
    return 2 * q + r, 2 * r


POINTS = _build_points()
POINT_SET = frozenset(POINTS)
POINT_TO_INDEX = {p: i for i, p in enumerate(POINTS)}

NEIGHBORS = {
    p: tuple(
        (p[0] + dq, p[1] + dr)
        for dq, dr in DIRECTIONS
        if (p[0] + dq, p[1] + dr) in POINT_SET
    )
    for p in POINTS
}

CORNERS = frozenset(
    p for p in POINTS if sum(1 for v in _cube(p) if abs(v) == RADIUS) == 2
)
BOUNDARY_POINTS = frozenset(
    p for p in POINTS if any(abs(v) == RADIUS for v in _cube(p))
)


def _build_sides():
    sides = []
    for axis, value in (
        ("q", RADIUS),
        ("q", -RADIUS),
        ("r", RADIUS),
        ("r", -RADIUS),
        ("s", RADIUS),
        ("s", -RADIUS),
    ):
        label = axis + "=" + _sign_label(value)
        pts = []
        for p in POINTS:
            q, r, s = _cube(p)
            coord = {"q": q, "r": r, "s": s}[axis]
            if coord == value and p not in CORNERS:
                pts.append(p)
        sides.append((label, frozenset(pts)))
    return tuple(sides)


SIDES = _build_sides()
POINT_TO_SIDE_LABELS = {
    p: tuple(label for label, side_points in SIDES if p in side_points)
    for p in POINTS
}


def _coord_to_label(point):
    q, r = point
    return "q{}_r{}".format(_action_sign_label(q), _action_sign_label(r))


def _coord_from_label(label):
    if not label.startswith("q"):
        raise ValueError("coordinate must start with q")
    parts = label[1:].split("_r")
    if len(parts) != 2:
        raise ValueError("coordinate must be q..._r...")
    q = _parse_action_sign_label(parts[0])
    r = _parse_action_sign_label(parts[1])
    point = (q, r)
    if point not in POINT_SET:
        raise ValueError("coordinate is not on the board")
    return point


@dataclass(frozen=True)
class GameState:
    board: tuple
    current: int
    remaining: tuple
    terminal: bool = False
    winner: object = None
    win_condition: str = ""
    move_number: int = 0
    last_action: str = ""


class Game:
    """Havannah implementation from the supplied rule pages."""

    num_players = 2

    def __init__(self):
        self.points = POINTS
        self.sides = SIDES
        self.corners = CORNERS

    def initial_state(self):
        return GameState(
            board=(EMPTY,) * len(POINTS),
            current=RED,
            remaining=(STONES_PER_PLAYER, STONES_PER_PLAYER),
        )

    def current_player(self, state):
        return TERMINAL if self.is_terminal(state) else state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        player = state.current
        if player not in (RED, BLACK) or state.remaining[player] <= 0:
            return []
        return [
            ("place", q, r)
            for i, (q, r) in enumerate(POINTS)
            if state.board[i] == EMPTY
        ]

    def apply_action(self, state, action):
        if self.is_terminal(state):
            raise ValueError("cannot act in a terminal state")

        action = self._normalize_action(action)
        _, q, r = action
        point = (q, r)
        idx = POINT_TO_INDEX[point]
        player = state.current

        if player not in (RED, BLACK):
            raise ValueError("bad current player")
        if state.remaining[player] <= 0:
            raise ValueError("current player has no stones remaining")
        if state.board[idx] != EMPTY:
            raise ValueError("point is occupied")

        board = list(state.board)
        board[idx] = player
        board = tuple(board)

        remaining = list(state.remaining)
        remaining[player] -= 1
        remaining = tuple(remaining)

        condition = self._winning_condition(board, player)
        next_player = BLACK if player == RED else RED

        if condition:
            return GameState(
                board=board,
                current=next_player,
                remaining=remaining,
                terminal=True,
                winner=player,
                win_condition=condition,
                move_number=state.move_number + 1,
                last_action=self.action_to_name(action),
            )

        terminal_draw = remaining[next_player] <= 0 or EMPTY not in board
        return GameState(
            board=board,
            current=next_player,
            remaining=remaining,
            terminal=terminal_draw,
            winner=None,
            win_condition="",
            move_number=state.move_number + 1,
            last_action=self.action_to_name(action),
        )

    def is_terminal(self, state):
        if state.terminal or state.winner is not None:
            return True
        if state.current not in (RED, BLACK):
            return True
        if state.remaining[state.current] <= 0:
            return True
        if EMPTY not in state.board:
            return True
        return False

    def returns(self, state):
        if not self.is_terminal(state):
            return [0.0, 0.0]
        if state.winner == RED:
            return [1.0, -1.0]
        if state.winner == BLACK:
            return [-1.0, 1.0]
        return [0.0, 0.0]

    def render(self, state):
        if self.is_terminal(state):
            turn = "terminal"
            result = "draw" if state.winner is None else (
                PLAYER_NAMES[state.winner] + ":" + state.win_condition
            )
        else:
            turn = PLAYER_NAMES[state.current]
            result = "ongoing"

        lines = [
            "turn={}; move={}; remaining=Red:{},Black:{}; result={}; last={}".format(
                turn,
                state.move_number,
                state.remaining[RED],
                state.remaining[BLACK],
                result,
                state.last_action or "-",
            ),
            "coords=axial(q,r); q increases left-to-right; .=empty R=red B=black",
        ]

        for r in range(-RADIUS, RADIUS + 1):
            q_min, q_max = _q_range_for_r(r)
            row = []
            for q in range(q_min, q_max + 1):
                row.append(SYMBOLS[state.board[POINT_TO_INDEX[(q, r)]]])
            indent = " " * abs(r)
            lines.append(
                "{}r={} q={}..{} | {}".format(
                    indent,
                    _sign_label(r),
                    _sign_label(q_min),
                    _sign_label(q_max),
                    " ".join(row),
                )
            )
        return "\n".join(lines)

    def action_to_name(self, action):
        action = self._normalize_action(action)
        _, q, r = action
        return "place:" + _coord_to_label((q, r))

    def name_to_action(self, name):
        if not isinstance(name, str) or not name.startswith("place:"):
            raise ValueError("bad action name")
        q, r = _coord_from_label(name[len("place:"):])
        return ("place", q, r)

    def _normalize_action(self, action):
        if isinstance(action, str):
            return self.name_to_action(action)
        if not isinstance(action, tuple) or len(action) != 3:
            raise ValueError("action must be ('place', q, r)")
        kind, q, r = action
        if kind != "place" or not isinstance(q, int) or not isinstance(r, int):
            raise ValueError("action must be ('place', q, r)")
        if (q, r) not in POINT_SET:
            raise ValueError("point is not on the board")
        return ("place", q, r)

    def _winning_condition(self, board, player):
        conditions = []
        if self._has_ring(board, player):
            conditions.append("ring")
        bridge, fork = self._has_bridge_and_fork(board, player)
        if bridge:
            conditions.append("bridge")
        if fork:
            conditions.append("fork")
        return "+".join(conditions)

    def _player_stones(self, board, player):
        return {POINTS[i] for i, value in enumerate(board) if value == player}

    def _has_bridge_and_fork(self, board, player):
        stones = self._player_stones(board, player)
        seen = set()
        has_bridge = False
        has_fork = False

        for start in stones:
            if start in seen:
                continue
            stack = [start]
            seen.add(start)
            component = []

            while stack:
                p = stack.pop()
                component.append(p)
                for nb in NEIGHBORS[p]:
                    if nb in stones and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)

            corner_count = sum(1 for p in component if p in CORNERS)
            side_labels = set()
            for p in component:
                side_labels.update(POINT_TO_SIDE_LABELS[p])

            if corner_count >= 2:
                has_bridge = True
            if len(side_labels) >= 3:
                has_fork = True
            if has_bridge and has_fork:
                return True, True

        return has_bridge, has_fork

    def _has_ring(self, board, player):
        # A ring is interpreted as a same-color cycle whose polygon contains
        # at least one board point, occupied or empty.
        stones = self._player_stones(board, player)
        if len(stones) < 6:
            return False

        unseen = set(stones)
        while unseen:
            start = unseen.pop()
            component = {start}
            stack = [start]
            edge_twice_count = 0

            while stack:
                p = stack.pop()
                for nb in NEIGHBORS[p]:
                    if nb in stones:
                        edge_twice_count += 1
                        if nb in unseen:
                            unseen.remove(nb)
                            component.add(nb)
                            stack.append(nb)

            edge_count = edge_twice_count // 2
            if edge_count >= len(component):
                if self._component_has_enclosing_cycle(component):
                    return True

        return False

    def _component_has_enclosing_cycle(self, component):
        adj = {}
        for p in component:
            px, py = _xy(p)
            ns = [nb for nb in NEIGHBORS[p] if nb in component]
            if ns:
                ns.sort(key=lambda n: math.atan2(_xy(n)[1] - py, _xy(n)[0] - px))
                adj[p] = ns

        directed_edges = [(p, nb) for p, ns in adj.items() for nb in ns]
        visited = set()

        for start_edge in directed_edges:
            if start_edge in visited:
                continue

            walk = []
            edge = start_edge
            while edge not in visited:
                visited.add(edge)
                u, v = edge
                walk.append(u)
                ns = adj[v]
                idx = ns.index(u)
                # Follow one face of the embedded graph.
                w = ns[(idx - 1) % len(ns)]
                edge = (v, w)

            for cycle in self._simple_cycles_from_closed_walk(walk):
                if self._cycle_encloses_board_point(cycle):
                    return True

        return False

    def _simple_cycles_from_closed_walk(self, walk):
        if not walk:
            return []
        sequence = list(walk) + [walk[0]]
        stack = []
        positions = {}
        cycles = []

        for v in sequence:
            if v in positions:
                i = positions[v]
                cycle = stack[i:]
                if len(cycle) >= 3:
                    cycles.append(tuple(cycle))
                for old in stack[i:]:
                    positions.pop(old, None)
                stack = stack[:i]
            positions[v] = len(stack)
            stack.append(v)

        return cycles

    def _cycle_encloses_board_point(self, cycle):
        cycle_set = set(cycle)
        poly = [_xy(p) for p in cycle]
        min_x = min(x for x, _ in poly)
        max_x = max(x for x, _ in poly)
        min_y = min(y for _, y in poly)
        max_y = max(y for _, y in poly)

        for p in POINTS:
            if p in cycle_set:
                continue
            x, y = _xy(p)
            if x < min_x or x > max_x or y < min_y or y > max_y:
                continue
            if self._point_strictly_inside_polygon((x, y), poly):
                return True
        return False

    def _point_strictly_inside_polygon(self, point, poly):
        x, y = point
        inside = False
        n = len(poly)

        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]

            cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
            if cross == 0 and min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
                return False

            if (y1 > y) != (y2 > y):
                x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x_intersect > x:
                    inside = not inside

        return inside
```