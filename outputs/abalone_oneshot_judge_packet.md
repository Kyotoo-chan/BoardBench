# BoardBench judge packet

- game: abalone

- OpenSpiel reference: none

- variant: oneshot

- generated code: outputs/abalone_oneshot.py

- expected judge reply path: outputs/abalone_oneshot_judge.md



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




## Rule text (inputs/game_rules.pdf)

ZIEL DES SPIELES
Als erster Spieler sechs Kugeln 
des Gegners vom Spielfeld zu 
schieben.
VORBEREITUNG
-  Setzen Sie die Kugeln wie in 
Abb. 1 gezeigt in ihre 
Startpositionen.
-  Losen Sie aus, welcher Spieler 
welche Farbe erhält.
Abbildung 1
DER SPIELABLAUF
-  Die Spieler sind abwechselnd 
an der Reihe. Schwarz fängt 
immer an.
-  In ihrem Zug dürfen Sie nur 
eine „Bewegung“ vornehmen – 
eigene Kugeln verschieben.
-  Eine Bewegung beinhaltet die 
Entfernung bis zur nächsten 
Mulde – nicht mehr.
-  Sie können eine Bewegung in 
eine der sechs möglichen 
Richtungen ausführen.
-  Sie dürfen eine Bewegung nur 
ausführen, wenn die angren-
zende Mulde frei ist.
-  Eine „Bewegung“ kann eine, 
zwei oder drei Kugeln 
umfassen. Wenn Sie zwei oder 
drei Kugeln gleichzeitig 
bewegen, so müssen alle in 
die gleiche Richtung gescho-
ben werden.
-  In einem Zug dürfen nicht mehr 
als drei Kugeln einer Farbe 
bewegt werden.
-  Sie dürfen eine vorhandene, 
längere Kugelreihe trennen, 
indem Sie eine, zwei oder drei 
Kugeln einer Farbe bewegen. 
Ein Spiel für 2 Spieler
SPIELANLEITUNG

Es gibt zwei Arten von 
 Bewegungen:
Abbildung 2
Eine Bewegung in gerader Linie: 
Die Kugeln werden geradeaus in die 
nächste Mulde geschoben.
Abbildung 3
Eine Bewegung zur Seite: 
Die Kugeln werden seitlich in die 
nächsten Mulden geschoben.
-  Ist eine Bewegung ausgeführt, 
kann sie nicht mehr verändert 
werden.
SUMITO
Sie können die Kugeln Ihres 
Gegners wegschieben, wenn 
Sie zuerst eine „Sumito“- 
Position aufbauen. Ein „Sumito“ 
ist eine Angriffs-Position, in der 
die Anzahl Ihrer Kugeln höher ist 
als die Ihres Gegners. Es gibt 
drei Sumito-Arten, die in den 
folgenden Beispielen zu sehen 
sind. Schwarz ist hier immer 
stärker als Weiß:
Abbildung 4
2- zu -1- Sumito
3- zu -1 - Sumito
3- zu -2 - Sumito
Wenn Sie eine Sumito-Position 
aufgebaut haben, so dürfen Sie 
die Kugeln Ihres Gegners nur 
wie folgt verschieben.
-  Durch eine Bewegung in 
gerader Linie.

-  Wenn sich schwarze und weiße 
Kugeln in direkt aneinander 
grenzenden Mulden befinden, 
und wenn sich hinter der oder 
den angegriffenen Kugeln eine 
freie Mulde befindet. 
Abbildung 5
In diesem Beispiel ist kein Sumito-
Angriff möglich. Schwarz kann Weiß 
nicht wegschieben, weil….
1   hier hinter der weißen Gruppe 
keine freie Mulde ist.
2   hier eine leere Mulde zwischen 
Schwarz und Weiß ist.
3   hier die Kugeln nicht in einer 
geraden Linie liegen.
Auch wenn ein Sumito-Angriff 
möglich ist, muss er nicht 
ausgführt werden. Der Spieler 
entscheidet, ob er angreifen will 
oder nicht.
PATT 
In einer Patt-Situation ist die 
Anzahl der Kugeln beider Spieler 
gleich: es ist keinem Spieler 
möglich, einen Vorteil zu 
erlangen.
Es gibt drei Arten von Patt-
Situationen:
Abbildung 6
1 - zu -1- Patt
2 - zu -2- Patt
3 - zu - 3- Patt
1
2
3

Hat ein Spieler mehr als drei 
Kugeln in einem Patt versammelt, 
so werden die überzähligen 
Kugeln nicht gezählt:
Ein 4 - zu - 3 zum Beispiel 
entspricht also einem  
3- zu - 3 Patt.
Um ein Patt aufzulösen, muss 
ein Spieler einen Angriff über 
eine andere Gerade starten  
(in einem anderen Winkel).
Abbildung 7
In diesem Beispiel bilden die Kugeln 
auf der Linie a-b ein Patt, so dass 
sie sich nicht gegenseitig 
wegschieben dürfen. Um das Patt 
aufzulösen, kann Schwarz auf der 
Linie c-d angreifen.
HINAUSSCHIEBEN
Eine Kugel ist aus dem Spiel, 
wenn sie aus dem Spielfeld 
hinaus auf den Rand geschoben 
wird.
Abbildung 8
Schwarz kann Weiß hinausschieben.
WER GEWINNT?
Der Spieler, der zuerst sechs 
Kugeln des Gegners hinaus 
geschoben hat, gewinnt das 
Spiel!
GEGEN DIE ZEIT
Wie beim Schach kann jedem 
Spieler eine bestimmte Spielzeit 
zugeteilt werden, zum Beispiel 
10 oder 15 Minuten. Offiizielle 
Abalone-Wettkämpfe werden 
immer gegen die Uhr gespielt.
Alle Rechte vorbehalten. Patent N° DM/012362
® Abalone ist ein registriertes Warenzeichen von Abalone s.a.
© Abalone s.a. - Domaine De Longue Plaine, 37250 Sorigny France
0 Schmidt Spiele GmbH, Postfach 470437, D-12313 Berlin 
www.schmidtspiele.de
Autoren: Laurent Lévi & Michel Lalet.



## Generated code (outputs/abalone_oneshot.py)

```python
"""Self-contained Abalone-like implementation from the provided German rules.

Known gap: Figure 1/start setup and exact board labels are missing.  The default
board/setup below is an explicit placeholder, not a claim of official layout.
"""

from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Optional, Set, Tuple

TERMINAL = -1
BLACK = 0
WHITE = 1
PLAYER_NAMES = ("B", "W")

Cell = Tuple[int, int]
Direction = Tuple[int, int]

DIRECTIONS: Tuple[Tuple[str, Direction], ...] = (
    ("E", (1, 0)),
    ("NE", (1, -1)),
    ("NW", (0, -1)),
    ("W", (-1, 0)),
    ("SW", (-1, 1)),
    ("SE", (0, 1)),
)
DIRECTION_BY_NAME = dict(DIRECTIONS)
AXES: Tuple[Direction, ...] = (
    DIRECTION_BY_NAME["E"],
    DIRECTION_BY_NAME["NE"],
    DIRECTION_BY_NAME["NW"],
)


def _coerce_cell(value) -> Cell:
    q, r = value
    if not isinstance(q, int) or not isinstance(r, int):
        raise ValueError("cell coordinates must be integers")
    return (q, r)


def _add(cell: Cell, direction: Direction, steps: int = 1) -> Cell:
    return (cell[0] + direction[0] * steps, cell[1] + direction[1] * steps)


def _neg(direction: Direction) -> Direction:
    return (-direction[0], -direction[1])


def _hex_cells(radius: int) -> FrozenSet[Cell]:
    return frozenset(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(-q - r)) <= radius
    )


def _encode_int(n: int) -> str:
    if n == 0:
        return "Z"
    return ("P" + str(n)) if n > 0 else ("N" + str(-n))


def _decode_int(text: str) -> int:
    if text == "Z":
        return 0
    if len(text) < 2 or text[0] not in ("P", "N") or not text[1:].isdigit():
        raise ValueError("bad signed coordinate")
    value = int(text[1:])
    return value if text[0] == "P" else -value


def _cell_label(cell: Cell) -> str:
    q, r = cell
    return "q%s_r%s" % (_encode_int(q), _encode_int(r))


def _parse_cell_label(label: str) -> Cell:
    parts = label.split("_")
    if len(parts) != 2 or not parts[0].startswith("q") or not parts[1].startswith("r"):
        raise ValueError("bad cell label")
    return (_decode_int(parts[0][1:]), _decode_int(parts[1][1:]))


def _canonical_cells(cells: Iterable[Cell]) -> Tuple[Cell, ...]:
    return tuple(sorted((_coerce_cell(c) for c in cells), key=_cell_label))


def _format_action(cells: Iterable[Cell], dir_name: str) -> str:
    if dir_name not in DIRECTION_BY_NAME:
        raise ValueError("bad direction")
    canonical = _canonical_cells(cells)
    if not 1 <= len(canonical) <= 3:
        raise ValueError("a move must name one, two, or three balls")
    if len(set(canonical)) != len(canonical):
        raise ValueError("duplicate cell in action")
    return "move:%s:%s" % (",".join(_cell_label(c) for c in canonical), dir_name)


def _parse_action_name(name: str) -> Tuple[Tuple[Cell, ...], str]:
    if not isinstance(name, str):
        raise TypeError("actions are canonical strings")
    if not name.startswith("move:"):
        raise ValueError("bad action prefix")
    body = name[len("move:") :]
    if ":" not in body:
        raise ValueError("bad action")
    cell_text, dir_name = body.rsplit(":", 1)
    if dir_name not in DIRECTION_BY_NAME:
        raise ValueError("bad direction")
    labels = cell_text.split(",")
    cells = tuple(_parse_cell_label(x) for x in labels if x)
    if len(cells) != len(labels):
        raise ValueError("empty cell label")
    if not 1 <= len(cells) <= 3:
        raise ValueError("a move must name one, two, or three balls")
    if len(set(cells)) != len(cells):
        raise ValueError("duplicate cell in action")
    return _canonical_cells(cells), dir_name


@dataclass(frozen=True)
class GameState:
    black: FrozenSet[Cell]
    white: FrozenSet[Cell]
    pushed_off_by: Tuple[int, int] = (0, 0)
    current: int = BLACK
    turn: int = 0
    winner: Optional[int] = None

    def __post_init__(self) -> None:
        black = frozenset(_coerce_cell(c) for c in self.black)
        white = frozenset(_coerce_cell(c) for c in self.white)
        if black & white:
            raise ValueError("a cell cannot contain both colors")
        scores = tuple(self.pushed_off_by)
        if len(scores) != 2 or any((not isinstance(x, int) or x < 0) for x in scores):
            raise ValueError("pushed_off_by must contain two non-negative integers")
        if self.current not in (BLACK, WHITE, TERMINAL):
            raise ValueError("bad current player")
        if self.winner not in (None, BLACK, WHITE):
            raise ValueError("bad winner")
        if not isinstance(self.turn, int) or self.turn < 0:
            raise ValueError("turn must be a non-negative integer")
        object.__setattr__(self, "black", black)
        object.__setattr__(self, "white", white)
        object.__setattr__(self, "pushed_off_by", scores)


class Game:
    """Two-player deterministic public-information game."""

    num_players = 2

    def __init__(
        self,
        radius: int = 3,
        black_positions: Optional[Iterable[Cell]] = None,
        white_positions: Optional[Iterable[Cell]] = None,
        target_pushed: int = 6,
    ):
        # Radius 3 is the smallest regular hex with a 7-cell line, allowing the
        # rulebook's described 4-to-3 Patt example. Exact board figure is absent.
        if not isinstance(radius, int) or radius < 3:
            raise ValueError("radius must be an integer at least 3")
        if not isinstance(target_pushed, int) or target_pushed <= 0:
            raise ValueError("target_pushed must be positive")
        self.radius = radius
        self.cells = _hex_cells(radius)
        self.target_pushed = target_pushed

        if black_positions is None:
            black = frozenset(c for c in self.cells if c[1] <= -radius + 1)
        else:
            black = self._coerce_positions(black_positions)

        if white_positions is None:
            white = frozenset(c for c in self.cells if c[1] >= radius - 1)
        else:
            white = self._coerce_positions(white_positions)

        outside = (black | white) - self.cells
        if outside:
            raise ValueError("initial position outside board: " + _cell_label(sorted(outside)[0]))
        if black & white:
            raise ValueError("initial black/white positions overlap")
        if len(black) < target_pushed or len(white) < target_pushed:
            raise ValueError("each side needs at least target_pushed balls")

        self.initial_black = black
        self.initial_white = white

    def _coerce_positions(self, positions: Iterable[Cell]) -> FrozenSet[Cell]:
        return frozenset(_coerce_cell(c) for c in positions)

    def initial_state(self) -> GameState:
        return GameState(
            black=self.initial_black,
            white=self.initial_white,
            pushed_off_by=(0, 0),
            current=BLACK,  # Black always starts.
            turn=0,
            winner=None,
        )

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.current

    def legal_actions(self, state: GameState) -> List[str]:
        if self._score_terminal(state):
            return []
        return self._legal_action_names(state)

    def apply_action(self, state: GameState, action: str) -> GameState:
        canonical = self.action_to_name(action)
        if canonical != action:
            raise ValueError("action is not canonical; use %r" % canonical)
        if canonical not in set(self.legal_actions(state)):
            raise ValueError("illegal action: %s" % canonical)

        cells, dir_name = _parse_action_name(canonical)
        delta = DIRECTION_BY_NAME[dir_name]
        player = state.current
        opponent = WHITE if player == BLACK else BLACK
        group = frozenset(cells)

        own_cells = set(self._player_cells(state, player))
        opponent_cells = set(self._player_cells(state, opponent))

        push_line: List[Cell] = []
        if len(group) > 1:
            axis = self._group_axis(group)
            if axis is not None and (delta == axis or delta == _neg(axis)):
                front = self._front_cell(group, delta)
                dest = _add(front, delta)
                if dest in opponent_cells:
                    push_line, _ = self._opponent_line(opponent_cells, dest, delta)

        for c in group:
            own_cells.remove(c)
        for c in group:
            own_cells.add(_add(c, delta))

        scores = list(state.pushed_off_by)
        if push_line:
            for c in push_line:
                opponent_cells.remove(c)
            for c in push_line:
                moved = _add(c, delta)
                if moved in self.cells:
                    opponent_cells.add(moved)
                else:
                    scores[player] += 1

        if player == BLACK:
            black, white = frozenset(own_cells), frozenset(opponent_cells)
        else:
            white, black = frozenset(own_cells), frozenset(opponent_cells)

        winner = player if scores[player] >= self.target_pushed else None
        return GameState(
            black=black,
            white=white,
            pushed_off_by=(scores[0], scores[1]),
            current=opponent,
            turn=state.turn + 1,
            winner=winner,
        )

    def is_terminal(self, state: GameState) -> bool:
        if self._score_terminal(state):
            return True
        # Rulebook does not define stalemate/no-move; assumption: draw terminal.
        return len(self._legal_action_names(state)) == 0

    def returns(self, state: GameState) -> Tuple[float, float]:
        winner = self._winner(state)
        if winner == BLACK:
            return (1.0, -1.0)
        if winner == WHITE:
            return (-1.0, 1.0)
        return (0.0, 0.0)

    def render(self, state: GameState) -> str:
        cp = self.current_player(state)
        current = "T" if cp == TERMINAL else PLAYER_NAMES[cp]
        winner = self._winner(state)
        winner_text = "-" if winner is None else PLAYER_NAMES[winner]
        lines = [
            "turn:%d current:%s pushed_off:B=%d,W=%d winner:%s"
            % (state.turn, current, state.pushed_off_by[0], state.pushed_off_by[1], winner_text)
        ]
        for r in range(-self.radius, self.radius + 1):
            row = sorted((c for c in self.cells if c[1] == r), key=lambda c: c[0])
            tokens = []
            for q, _ in row:
                cell = (q, r)
                mark = "B" if cell in state.black else ("W" if cell in state.white else ".")
                tokens.append("q%s=%s" % (_encode_int(q), mark))
            lines.append("r%s:%s" % (_encode_int(r), " ".join(tokens)))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        cells, dir_name = _parse_action_name(action)
        return _format_action(cells, dir_name)

    def name_to_action(self, name: str) -> str:
        canonical = self.action_to_name(name)
        if canonical != name:
            raise ValueError("not a canonical action name")
        return name

    def _winner(self, state: GameState) -> Optional[int]:
        if state.winner is not None:
            return state.winner
        b, w = state.pushed_off_by
        if b >= self.target_pushed and w < self.target_pushed:
            return BLACK
        if w >= self.target_pushed and b < self.target_pushed:
            return WHITE
        return None

    def _score_terminal(self, state: GameState) -> bool:
        return (
            state.winner is not None
            or state.pushed_off_by[BLACK] >= self.target_pushed
            or state.pushed_off_by[WHITE] >= self.target_pushed
        )

    def _player_cells(self, state: GameState, player: int) -> FrozenSet[Cell]:
        if player == BLACK:
            return state.black
        if player == WHITE:
            return state.white
        return frozenset()

    def _legal_action_names(self, state: GameState) -> List[str]:
        if self._score_terminal(state) or state.current not in (BLACK, WHITE):
            return []
        own = self._player_cells(state, state.current)
        actions: Set[str] = set()
        for group in self._groups(own):
            for dir_name, delta in DIRECTIONS:
                if self._can_move(state, group, delta):
                    actions.add(_format_action(group, dir_name))
        return sorted(actions)

    def _groups(self, own: FrozenSet[Cell]) -> List[Tuple[Cell, ...]]:
        groups: Set[FrozenSet[Cell]] = set()
        for cell in own:
            groups.add(frozenset((cell,)))
        for axis in AXES:
            for cell in own:
                for length in (2, 3):
                    seq = tuple(_add(cell, axis, i) for i in range(length))
                    if all(c in own for c in seq):
                        groups.add(frozenset(seq))
        return sorted(
            (tuple(sorted(g, key=_cell_label)) for g in groups),
            key=lambda g: (len(g), ",".join(_cell_label(c) for c in g)),
        )

    def _group_axis(self, group: Iterable[Cell]) -> Optional[Direction]:
        group_set = frozenset(group)
        n = len(group_set)
        if n <= 1:
            return None
        for axis in AXES:
            for start in group_set:
                if frozenset(_add(start, axis, i) for i in range(n)) == group_set:
                    return axis
        return None

    def _front_cell(self, group: Iterable[Cell], delta: Direction) -> Cell:
        group_set = frozenset(group)
        fronts = [c for c in group_set if _add(c, delta) not in group_set]
        if len(fronts) != 1:
            raise ValueError("group has no unique front in this direction")
        return fronts[0]

    def _opponent_line(
        self, opponent_cells: Iterable[Cell], start: Cell, delta: Direction
    ) -> Tuple[List[Cell], Cell]:
        opponent_set = set(opponent_cells)
        line: List[Cell] = []
        cursor = start
        while cursor in opponent_set:
            line.append(cursor)
            cursor = _add(cursor, delta)
        return line, cursor

    def _can_move(self, state: GameState, group: Iterable[Cell], delta: Direction) -> bool:
        group_set = frozenset(group)
        if not 1 <= len(group_set) <= 3:
            return False

        player = state.current
        own = self._player_cells(state, player)
        opponent = self._player_cells(state, WHITE if player == BLACK else BLACK)
        occupied = state.black | state.white

        if not group_set <= own:
            return False

        if len(group_set) == 1:
            dest = _add(next(iter(group_set)), delta)
            return dest in self.cells and dest not in occupied

        axis = self._group_axis(group_set)
        if axis is None:
            return False

        inline = delta == axis or delta == _neg(axis)

        if not inline:
            # Side movement: every selected ball moves into a free adjacent hole.
            return all(_add(c, delta) in self.cells and _add(c, delta) not in occupied for c in group_set)

        front = self._front_cell(group_set, delta)
        dest = _add(front, delta)

        if dest not in self.cells:
            return False
        if dest not in occupied:
            return True
        if dest in own:
            return False

        # Sumito: straight-line push only, attacker count must exceed defender count.
        opp_line, after = self._opponent_line(opponent, dest, delta)
        if len(group_set) <= len(opp_line):
            return False
        if len(opp_line) > 2:
            return False

        # Behind the attacked balls must be empty, or off-board for pushing out.
        if after in self.cells:
            return after not in occupied
        return True
```