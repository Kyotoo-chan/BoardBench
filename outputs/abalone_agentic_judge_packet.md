# BoardBench judge packet

- game: abalone

- OpenSpiel reference: none

- variant: agentic

- generated code: outputs/abalone_agentic.py

- expected judge reply path: outputs/abalone_agentic_judge.md



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



## Generated code (outputs/abalone_agentic.py)

```python
"""Self-contained Abalone implementation from the supplied German rulebook.

Documented assumptions where the rulebook text/figures are incomplete:
- The board is the hexagonal field shown in Fig. 1: nine rows with lengths
  5, 6, 7, 8, 9, 8, 7, 6, 5.
- The initial position is read from Fig. 1 as black on the top two rows plus
  the center three holes of the third row, and white mirrored at the bottom.
- The rulebook gives no coordinate labels, so this implementation labels holes
  by display row/column (R1C1 is the top-left hole).
- A two- or three-marble move selects contiguous own marbles in one straight
  line.  Longer lines may be split by selecting a contiguous window of 1-3.
- Sumito pushes may push the last opposing marble off the board, because the
  "Hinausschieben" section describes a marble leaving the field when pushed
  onto the rim.  Equal-strength Patt positions are illegal pushes because a
  push requires strictly more attacking marbles than defending marbles.
- Chess-clock play, draws, repetition, resignation, and tournament procedures
  are not specified and are not modeled.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

TERMINAL = -1

EMPTY = "."
PLAYER_PIECES = ("B", "W")  # player 0 is black; player 1 is white.
PLAYER_NAMES = ("black", "white")
WIN_PUSHED_OFF = 6

Coord = Tuple[int, int]

# Axial hex directions.  With rows rendered top-to-bottom, E/W stay in a row,
# SE/SW move down, and NE/NW move up.
DIRECTIONS: Dict[str, Coord] = {
    "E": (1, 0),
    "SE": (0, 1),
    "SW": (-1, 1),
    "W": (-1, 0),
    "NW": (0, -1),
    "NE": (1, -1),
}
DIRECTION_NAMES = ("E", "SE", "SW", "W", "NW", "NE")
OPPOSITE = {"E": "W", "W": "E", "SE": "NW", "NW": "SE", "SW": "NE", "NE": "SW"}
# One representative for each of the three straight-line axes.
AXIS_NAMES = ("E", "SE", "NE")

ROW_LENGTHS = (5, 6, 7, 8, 9, 8, 7, 6, 5)

CELLS: List[Coord] = []
CELL_TO_LABEL: Dict[Coord, str] = {}
LABEL_TO_CELL: Dict[str, Coord] = {}
ROW_CELLS: List[Tuple[Coord, ...]] = []

for row_number, r in enumerate(range(-4, 5), start=1):
    q_min = max(-4, -r - 4)
    q_max = min(4, -r + 4)
    row: List[Coord] = []
    for col_number, q in enumerate(range(q_min, q_max + 1), start=1):
        cell = (q, r)
        label = f"R{row_number}C{col_number}"
        CELLS.append(cell)
        row.append(cell)
        CELL_TO_LABEL[cell] = label
        LABEL_TO_CELL[label] = cell
    ROW_CELLS.append(tuple(row))

CELL_TO_INDEX: Dict[Coord, int] = {cell: i for i, cell in enumerate(CELLS)}
INDEX_TO_CELL: Tuple[Coord, ...] = tuple(CELLS)
CELL_COUNT = len(CELLS)


def _add(cell: Coord, direction: Coord) -> Coord:
    return (cell[0] + direction[0], cell[1] + direction[1])


def _neg(direction: Coord) -> Coord:
    return (-direction[0], -direction[1])


def _on_board(cell: Coord) -> bool:
    return cell in CELL_TO_INDEX


def _piece_at(board: Sequence[str], cell: Coord) -> str:
    return board[CELL_TO_INDEX[cell]]


def _label(cell: Coord) -> str:
    return CELL_TO_LABEL[cell]


def _labels(cells: Iterable[Coord]) -> List[str]:
    return [_label(cell) for cell in sorted(cells, key=lambda c: CELL_TO_INDEX[c])]


def _source_text(cells: Iterable[Coord]) -> str:
    return "+".join(_labels(cells))


def _cells_from_source_text(text: str) -> Tuple[Coord, ...]:
    if not text:
        raise ValueError("empty source list")
    cells = []
    for part in text.split("+"):
        if part not in LABEL_TO_CELL:
            raise ValueError(f"unknown cell label: {part}")
        cells.append(LABEL_TO_CELL[part])
    return tuple(cells)


def _front_cell(group: Sequence[Coord], direction: Coord) -> Coord:
    group_set = set(group)
    fronts = [cell for cell in group if _add(cell, direction) not in group_set]
    if len(fronts) != 1:
        raise ValueError("group is not a single contiguous line in that direction")
    return fronts[0]


def _ordered_front_to_back(group: Sequence[Coord], direction: Coord) -> List[Coord]:
    group_set = set(group)
    ordered = [_front_cell(group, direction)]
    back_step = _neg(direction)
    while True:
        nxt = _add(ordered[-1], back_step)
        if nxt not in group_set:
            return ordered
        ordered.append(nxt)


def _initial_board() -> Tuple[str, ...]:
    board = [EMPTY] * CELL_COUNT

    def set_piece(label: str, piece: str) -> None:
        board[CELL_TO_INDEX[LABEL_TO_CELL[label]]] = piece

    # Fig. 1 setup, using the implementation's row/column labels.
    for label in ("R1C1", "R1C2", "R1C3", "R1C4", "R1C5"):
        set_piece(label, "B")
    for label in ("R2C1", "R2C2", "R2C3", "R2C4", "R2C5", "R2C6"):
        set_piece(label, "B")
    for label in ("R3C3", "R3C4", "R3C5"):
        set_piece(label, "B")

    for label in ("R9C1", "R9C2", "R9C3", "R9C4", "R9C5"):
        set_piece(label, "W")
    for label in ("R8C1", "R8C2", "R8C3", "R8C4", "R8C5", "R8C6"):
        set_piece(label, "W")
    for label in ("R7C3", "R7C4", "R7C5"):
        set_piece(label, "W")

    return tuple(board)


INITIAL_BOARD = _initial_board()


@dataclass(frozen=True)
class GameState:
    board: Tuple[str, ...]
    to_move: int = 0
    pushed_off: Tuple[int, int] = (0, 0)  # opponent marbles pushed off by each player
    winner: Optional[int] = None
    history: Tuple[str, ...] = ()


class Game:
    """Minimal deterministic two-player Abalone API."""

    num_players = 2
    player_names = PLAYER_NAMES

    def initial_state(self) -> GameState:
        return GameState(board=INITIAL_BOARD, to_move=0, pushed_off=(0, 0), winner=None, history=())

    def current_player(self, state: GameState) -> int:
        return TERMINAL if self.is_terminal(state) else state.to_move

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        return sorted(_legal_actions(state))

    def apply_action(self, state: GameState, action: str) -> GameState:
        action = self.action_to_name(action)
        legal = set(self.legal_actions(state))
        if action not in legal:
            raise ValueError(f"illegal action for this state: {action}")

        kind, mode, sources, direction_name = _parse_action(action)
        direction = DIRECTIONS[direction_name]
        board = list(state.board)
        player = state.to_move
        pushed_off = list(state.pushed_off)

        if kind == "push":
            if _apply_push(board, sources, direction, player):
                pushed_off[player] += 1
        elif mode in ("single", "line"):
            _apply_line_move(board, sources, direction)
        elif mode == "side":
            _apply_side_move(board, sources, direction)
        else:  # The parser should prevent this.
            raise ValueError(f"unknown action mode: {mode}")

        winner: Optional[int] = None
        for p, count in enumerate(pushed_off):
            if count >= WIN_PUSHED_OFF:
                winner = p
                break

        next_player = 1 - player
        return GameState(
            board=tuple(board),
            to_move=next_player,
            pushed_off=(pushed_off[0], pushed_off[1]),
            winner=winner,
            history=state.history + (action,),
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or any(count >= WIN_PUSHED_OFF for count in state.pushed_off)

    def returns(self, state: GameState) -> List[float]:
        winner = state.winner
        if winner is None:
            for p, count in enumerate(state.pushed_off):
                if count >= WIN_PUSHED_OFF:
                    winner = p
                    break
        if winner is None:
            return [0.0, 0.0]
        return [1.0 if p == winner else -1.0 for p in range(self.num_players)]

    def render(self, state: GameState) -> str:
        turn = "terminal" if self.is_terminal(state) else PLAYER_PIECES[state.to_move]
        lines = [
            f"turn:{turn} pushed_off:B={state.pushed_off[0]} W={state.pushed_off[1]}",
        ]
        for row_number, row in enumerate(ROW_CELLS, start=1):
            contents = " ".join(_piece_at(state.board, cell) for cell in row)
            lines.append(f"R{row_number}: {contents}")
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are represented by their canonical string names")
        # Validate syntax, but not state-specific legality.
        _parse_action(action)
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names must be strings")
        _parse_action(name)
        return name


def _parse_action(action: str) -> Tuple[str, str, Tuple[Coord, ...], str]:
    parts = action.split(":")
    if len(parts) == 4 and parts[0] == "move":
        mode = parts[1]
        if mode not in ("single", "line", "side"):
            raise ValueError(f"unknown move mode: {mode}")
        sources = _cells_from_source_text(parts[2])
        direction_name = parts[3]
        kind = "move"
    elif len(parts) == 3 and parts[0] == "push":
        mode = "push"
        sources = _cells_from_source_text(parts[1])
        direction_name = parts[2]
        kind = "push"
    else:
        raise ValueError(f"not a canonical action name: {action}")

    if direction_name not in DIRECTIONS:
        raise ValueError(f"unknown direction: {direction_name}")
    if len(set(sources)) != len(sources):
        raise ValueError("duplicate source in action")
    if mode == "single" and len(sources) != 1:
        raise ValueError("single moves need exactly one source")
    if mode in ("line", "side", "push") and len(sources) not in (2, 3):
        raise ValueError("line, side, and push moves need two or three sources")
    return kind, mode, sources, direction_name


def _legal_actions(state: GameState) -> List[str]:
    board = state.board
    player = state.to_move
    own = PLAYER_PIECES[player]
    opp = PLAYER_PIECES[1 - player]
    actions = set()

    own_cells = [cell for cell in CELLS if _piece_at(board, cell) == own]

    # One-marble moves: the adjacent target hole must be on the board and empty.
    for cell in own_cells:
        for direction_name in DIRECTION_NAMES:
            direction = DIRECTIONS[direction_name]
            dest = _add(cell, direction)
            if _on_board(dest) and _piece_at(board, dest) == EMPTY:
                actions.add(f"move:single:{_label(cell)}:{direction_name}")

    # Two- and three-marble straight contiguous groups.
    for group, axis_name in _candidate_groups(board, own):
        source = _source_text(group)
        for direction_name in DIRECTION_NAMES:
            direction = DIRECTIONS[direction_name]
            if direction_name in (axis_name, OPPOSITE[axis_name]):
                inline = _inline_move_kind(board, group, direction, own, opp)
                if inline == "line":
                    actions.add(f"move:line:{source}:{direction_name}")
                elif inline == "push":
                    actions.add(f"push:{source}:{direction_name}")
            else:
                if _side_move_is_legal(board, group, direction):
                    actions.add(f"move:side:{source}:{direction_name}")

    return list(actions)


def _candidate_groups(board: Sequence[str], own_piece: str) -> Iterable[Tuple[Tuple[Coord, ...], str]]:
    for axis_name in AXIS_NAMES:
        step = DIRECTIONS[axis_name]
        for start in CELLS:
            for size in (2, 3):
                group = tuple((start[0] + i * step[0], start[1] + i * step[1]) for i in range(size))
                if all(_on_board(cell) and _piece_at(board, cell) == own_piece for cell in group):
                    yield group, axis_name


def _inline_move_kind(
    board: Sequence[str], group: Sequence[Coord], direction: Coord, own_piece: str, opp_piece: str
) -> Optional[str]:
    front = _front_cell(group, direction)
    first = _add(front, direction)
    if not _on_board(first):
        return None

    first_piece = _piece_at(board, first)
    if first_piece == EMPTY:
        return "line"
    if first_piece != opp_piece:
        return None

    defenders = []
    cur = first
    while _on_board(cur) and _piece_at(board, cur) == opp_piece:
        defenders.append(cur)
        cur = _add(cur, direction)

    # Sumito: only 2-vs-1, 3-vs-1, and 3-vs-2. Equal Patt cannot push.
    if len(defenders) not in (1, 2):
        return None
    if len(group) <= len(defenders):
        return None
    if not _on_board(cur) or _piece_at(board, cur) == EMPTY:
        return "push"
    return None


def _side_move_is_legal(board: Sequence[str], group: Sequence[Coord], direction: Coord) -> bool:
    for cell in group:
        dest = _add(cell, direction)
        if not _on_board(dest) or _piece_at(board, dest) != EMPTY:
            return False
    return True


def _apply_line_move(board: List[str], group: Sequence[Coord], direction: Coord) -> None:
    for cell in _ordered_front_to_back(group, direction):
        dest = _add(cell, direction)
        board[CELL_TO_INDEX[dest]] = board[CELL_TO_INDEX[cell]]
        board[CELL_TO_INDEX[cell]] = EMPTY


def _apply_side_move(board: List[str], group: Sequence[Coord], direction: Coord) -> None:
    piece = board[CELL_TO_INDEX[group[0]]]
    for cell in group:
        board[CELL_TO_INDEX[cell]] = EMPTY
    for cell in group:
        dest = _add(cell, direction)
        board[CELL_TO_INDEX[dest]] = piece


def _apply_push(board: List[str], group: Sequence[Coord], direction: Coord, player: int) -> bool:
    opp_piece = PLAYER_PIECES[1 - player]
    front = _front_cell(group, direction)
    cur = _add(front, direction)
    defenders: List[Coord] = []
    while _on_board(cur) and board[CELL_TO_INDEX[cur]] == opp_piece:
        defenders.append(cur)
        cur = _add(cur, direction)

    pushed_one_off = not _on_board(cur)
    if pushed_one_off:
        # The farthest defender leaves the board; the rest slide forward.
        farthest = defenders[-1]
        board[CELL_TO_INDEX[farthest]] = EMPTY
        defenders_to_move = defenders[:-1]
    else:
        defenders_to_move = defenders

    for defender in reversed(defenders_to_move):
        dest = _add(defender, direction)
        board[CELL_TO_INDEX[dest]] = opp_piece
        board[CELL_TO_INDEX[defender]] = EMPTY

    _apply_line_move(board, group, direction)
    return pushed_one_off
```