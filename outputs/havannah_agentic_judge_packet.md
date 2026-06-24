# BoardBench judge packet

- game: havannah

- OpenSpiel reference: havannah(board_size=8)

- variant: agentic

- generated code: outputs/havannah_agentic.py

- expected judge reply path: outputs/havannah_agentic_judge.md



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



## Generated code (outputs/havannah_agentic.py)

```python
"""Rulebook-derived implementation of Havannah.

Source rules used here (translated/summarized from the supplied rulebook):
- Two players: red and black; red starts.
- The board has 169 intersection points.
- Players alternate placing one stone of their colour on a free point; stones do not move.
- A player wins immediately by first making a ring, bridge, or fork.

Assumptions needed for a programmatic API:
- The colour draw is not modeled; player 0 is red and player 1 is black.
- The 169-point board is represented as a hexagonal triangular-lattice board with
  radius 7 (side length 8), which has exactly 169 points.
- The component list says there are 55 stones of each colour; this implementation
  treats that as a strict supply. If the side to move has no stone left (or no
  free point exists) and nobody has won, the game is a draw.
- The rulebook gives no coordinate labels, so stable axial coordinates (q, r) are
  used in action names, with signs encoded as p/n/z.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

Coord = Tuple[int, int]
Action = Coord

NUM_PLAYERS = 2
RED = 0
BLACK = 1
PLAYER_NAMES = ("red", "black")
PLAYER_TOKENS = ("R", "B")
BOARD_RADIUS = 7
STONE_SUPPLY = 55

_NEIGHBOR_DELTAS: Tuple[Coord, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass
class GameState:
    """Public state for Havannah.

    board maps occupied coordinates to player numbers: 0 for red, 1 for black.
    apply_action returns a fresh GameState and does not mutate the input state.
    """

    board: Dict[Coord, int] = field(default_factory=dict)
    to_play: int = RED
    move_number: int = 0
    winner: Optional[int] = None
    win_type: Optional[str] = None
    history: Tuple[Tuple[int, Coord], ...] = ()


class Game:
    """A small, self-contained Havannah engine."""

    def __init__(self) -> None:
        self.num_players = NUM_PLAYERS
        self.radius = BOARD_RADIUS
        self.stone_supply = STONE_SUPPLY
        self.coords: Tuple[Coord, ...] = tuple(self._make_coords(self.radius))
        self.coord_set: Set[Coord] = set(self.coords)
        self.corners: Tuple[Coord, ...] = (
            (self.radius, 0),
            (self.radius, -self.radius),
            (0, -self.radius),
            (-self.radius, 0),
            (-self.radius, self.radius),
            (0, self.radius),
        )
        self.corner_set: Set[Coord] = set(self.corners)
        self.corner_index = {coord: i for i, coord in enumerate(self.corners)}
        self.side_indices = {coord: self._side_indices_for(coord) for coord in self.coords}
        self.boundary_set: Set[Coord] = {
            coord for coord in self.coords if self._is_boundary(coord)
        }

    # ----- Required API -------------------------------------------------

    def initial_state(self) -> GameState:
        return GameState()

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        return state.to_play

    def legal_actions(self, state: GameState) -> List[Action]:
        if state.winner is not None:
            return []
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            return []
        if len(state.board) >= len(self.coords):
            return []
        return [coord for coord in self.coords if coord not in state.board]

    def apply_action(self, state: GameState, action: Union[Action, str]) -> GameState:
        if self.is_terminal(state):
            raise ValueError("cannot apply an action to a terminal state")

        coord = self._coerce_action(action)
        if coord not in self.coord_set:
            raise ValueError(f"action is outside the board: {coord!r}")
        if coord in state.board:
            raise ValueError(f"point is already occupied: {self._coord_label(coord)}")
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            raise ValueError(f"{PLAYER_NAMES[state.to_play]} has no stones left")

        player = state.to_play
        new_board = dict(state.board)
        new_board[coord] = player
        new_history = state.history + ((player, coord),)

        win_types = self._winning_figures(new_board, player)
        if win_types:
            return GameState(
                board=new_board,
                to_play=1 - player,
                move_number=state.move_number + 1,
                winner=player,
                win_type="+".join(win_types),
                history=new_history,
            )

        return GameState(
            board=new_board,
            to_play=1 - player,
            move_number=state.move_number + 1,
            winner=None,
            win_type=None,
            history=new_history,
        )

    def is_terminal(self, state: GameState) -> bool:
        if state.winner is not None:
            return True
        if self._player_stone_count(state.board, state.to_play) >= self.stone_supply:
            return True
        if len(state.board) >= len(self.coords):
            return True
        return False

    def returns(self, state: GameState) -> List[float]:
        if state.winner is None:
            return [0.0, 0.0]
        return [1.0 if player == state.winner else -1.0 for player in range(NUM_PLAYERS)]

    def render(self, state: GameState) -> str:
        if state.winner is not None:
            status = f"terminal winner={PLAYER_NAMES[state.winner]} win={state.win_type}"
        elif self.is_terminal(state):
            status = "terminal draw"
        else:
            status = f"to_play={PLAYER_NAMES[state.to_play]}"

        red_count = self._player_stone_count(state.board, RED)
        black_count = self._player_stone_count(state.board, BLACK)
        lines = [
            f"Havannah radius={self.radius} points={len(self.coords)} move={state.move_number} {status}",
            f"counts red={red_count}/{self.stone_supply} black={black_count}/{self.stone_supply}",
            "legend R=red B=black .=empty; coordinates are axial q,r",
        ]

        for r in range(-self.radius, self.radius + 1):
            q_min, q_max = self._q_range_for_r(r)
            row_len = q_max - q_min + 1
            indent = " " * (2 * self.radius + 1 - row_len)
            cells = []
            for q in range(q_min, q_max + 1):
                owner = state.board.get((q, r))
                cells.append("." if owner is None else PLAYER_TOKENS[owner])
            lines.append(
                f"{indent}r{self._signed_label(r)} q{self._signed_label(q_min)}..q{self._signed_label(q_max)} | "
                + " ".join(cells)
            )
        return "\n".join(lines)

    def action_to_name(self, action: Union[Action, str]) -> str:
        coord = self._coerce_action(action)
        if coord not in self.coord_set:
            raise ValueError(f"action is outside the board: {coord!r}")
        q, r = coord
        return f"place:q{self._signed_label(q)}_r{self._signed_label(r)}"

    def name_to_action(self, name: str) -> Action:
        if not isinstance(name, str) or not name.startswith("place:q"):
            raise ValueError(f"not a canonical Havannah action name: {name!r}")
        rest = name[len("place:q") :]
        if "_r" not in rest:
            raise ValueError(f"not a canonical Havannah action name: {name!r}")
        q_text, r_text = rest.split("_r", 1)
        q = self._parse_signed_label(q_text)
        r = self._parse_signed_label(r_text)
        coord = (q, r)
        if coord not in self.coord_set:
            raise ValueError(f"action name is outside the board: {name!r}")
        if self.action_to_name(coord) != name:
            raise ValueError(f"non-canonical Havannah action name: {name!r}")
        return coord

    # ----- Board construction and names --------------------------------

    @staticmethod
    def _make_coords(radius: int) -> List[Coord]:
        coords: List[Coord] = []
        for r in range(-radius, radius + 1):
            q_min = max(-radius, -r - radius)
            q_max = min(radius, -r + radius)
            for q in range(q_min, q_max + 1):
                coords.append((q, r))
        return coords

    def _q_range_for_r(self, r: int) -> Tuple[int, int]:
        return max(-self.radius, -r - self.radius), min(self.radius, -r + self.radius)

    @staticmethod
    def _signed_label(value: int) -> str:
        if value == 0:
            return "z0"
        if value > 0:
            return f"p{value}"
        return f"n{-value}"

    @staticmethod
    def _parse_signed_label(text: str) -> int:
        if len(text) < 2 or text[0] not in "pnz" or not text[1:].isdigit():
            raise ValueError(f"bad signed coordinate label: {text!r}")
        value = int(text[1:])
        if text[0] == "z":
            if value != 0:
                raise ValueError(f"zero coordinate must be z0, not {text!r}")
            return 0
        if value == 0:
            raise ValueError(f"non-zero coordinate label cannot use zero: {text!r}")
        return value if text[0] == "p" else -value

    def _coord_label(self, coord: Coord) -> str:
        return f"q{self._signed_label(coord[0])}_r{self._signed_label(coord[1])}"

    def _coerce_action(self, action: Union[Action, str]) -> Action:
        if isinstance(action, str):
            return self.name_to_action(action)
        if (
            isinstance(action, tuple)
            and len(action) == 2
            and isinstance(action[0], int)
            and isinstance(action[1], int)
        ):
            return action
        raise ValueError(f"action must be a coordinate tuple or canonical name: {action!r}")

    # ----- Geometry ------------------------------------------------------

    def _neighbors(self, coord: Coord) -> Iterable[Coord]:
        q, r = coord
        for dq, dr in _NEIGHBOR_DELTAS:
            neighbor = (q + dq, r + dr)
            if neighbor in self.coord_set:
                yield neighbor

    def _is_boundary(self, coord: Coord) -> bool:
        q, r = coord
        s = q + r
        return (
            abs(q) == self.radius
            or abs(r) == self.radius
            or abs(s) == self.radius
        )

    def _side_indices_for(self, coord: Coord) -> Tuple[int, ...]:
        """Return side indices touched by coord; corners deliberately return ()."""
        if coord in self.corner_set:
            return ()
        q, r = coord
        s = q + r
        sides: List[int] = []
        if q == self.radius:
            sides.append(0)
        if r == -self.radius:
            sides.append(1)
        if s == -self.radius:
            sides.append(2)
        if q == -self.radius:
            sides.append(3)
        if r == self.radius:
            sides.append(4)
        if s == self.radius:
            sides.append(5)
        return tuple(sides)

    # ----- Win detection -------------------------------------------------

    def _winning_figures(self, board: Dict[Coord, int], player: int) -> List[str]:
        wins: List[str] = []
        bridge, fork = self._bridge_and_fork(board, player)
        if self._has_ring(board, player):
            wins.append("ring")
        if bridge:
            wins.append("bridge")
        if fork:
            wins.append("fork")
        return wins

    def _bridge_and_fork(self, board: Dict[Coord, int], player: int) -> Tuple[bool, bool]:
        stones = {coord for coord, owner in board.items() if owner == player}
        unseen = set(stones)
        bridge = False
        fork = False

        while unseen:
            start = unseen.pop()
            stack = [start]
            corners_touched: Set[int] = set()
            sides_touched: Set[int] = set()

            while stack:
                coord = stack.pop()
                if coord in self.corner_index:
                    corners_touched.add(self.corner_index[coord])
                sides_touched.update(self.side_indices[coord])

                for neighbor in self._neighbors(coord):
                    if neighbor in unseen and board.get(neighbor) == player:
                        unseen.remove(neighbor)
                        stack.append(neighbor)

            if len(corners_touched) >= 2:
                bridge = True
            if len(sides_touched) >= 3:
                fork = True
            if bridge and fork:
                break

        return bridge, fork

    def _has_ring(self, board: Dict[Coord, int], player: int) -> bool:
        """Detect a closed connection enclosing at least one board point.

        A point is enclosed if, after treating the player's other stones as
        blockers, that point cannot reach any board boundary point. This checks
        empty/opponent points and also own stones that may already occupy the
        interior, matching the rulebook note that enclosed points may be occupied
        by anyone.
        """
        player_stones = {coord for coord, owner in board.items() if owner == player}
        if len(player_stones) < 6:
            return False

        for point in self.coords:
            if point in self.boundary_set:
                continue
            blocked = player_stones - ({point} if point in player_stones else set())
            if not self._can_reach_boundary(point, blocked):
                return True
        return False

    def _can_reach_boundary(self, start: Coord, blocked: Set[Coord]) -> bool:
        if start in blocked:
            return False
        if start in self.boundary_set:
            return True

        seen = {start}
        stack = [start]
        while stack:
            coord = stack.pop()
            for neighbor in self._neighbors(coord):
                if neighbor in blocked or neighbor in seen:
                    continue
                if neighbor in self.boundary_set:
                    return True
                seen.add(neighbor)
                stack.append(neighbor)
        return False

    @staticmethod
    def _player_stone_count(board: Dict[Coord, int], player: int) -> int:
        return sum(1 for owner in board.values() if owner == player)
```