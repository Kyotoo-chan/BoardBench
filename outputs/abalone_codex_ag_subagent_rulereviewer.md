Warning: No models match pattern "anthropic/claude-opus-4-8"
Task: Read `canonical_rulebook.pdf`, all `canonical-page-*.jpg`, `canonical_rulefacts.md`, and `implementation.py`. Apply the BoardBench review evidence rules from your role. Return a concise evidence-backed review with severity-ranked findings, rule-area coverage, missing deterministic tests, questions, and a final score/confidence block. Do not edit files and do not inspect anything outside this workspace.
---
**Output:**
Write your findings to exactly this path: C:\Users\benti\AppData\Local\Temp\boardbench-abalone-review-T8Ieib\.pi-subagents\artifacts\outputs\0d273e0a-fb8a-40f7-a716-7e9746c3abff\subagent_rulereviewer.md
This path is authoritative for this run.
Ignore any other output filename or output path mentioned elsewhere, including output destinations in the base agent prompt, system prompt, or task instructions.
## Acceptance Contract
Acceptance level: reviewed
Completion is not accepted from prose alone. End with a structured acceptance report.
Criteria:
- criterion-1: Implement the requested change without widening scope
- criterion-2: Return evidence sufficient for an independent acceptance review
Required evidence: changed-files, tests-added, commands-run, validation-output, residual-risks, no-staged-files
Review gate: required by reviewer.
Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```
ls: .
.pi-subagents/
canonical_rulebook.pdf
canonical_rulefacts.md
canonical-page-1.jpg
canonical-page-2.jpg
canonical-page-3.jpg
canonical-page-4.jpg
implementation.py
read: canonical_rulefacts.md
read: implementation.py
read: canonical_rulebook.pdf
read: canonical-page-1.jpg
read: canonical-page-2.jpg
read: canonical-page-3.jpg
read: canonical-page-4.jpg
---
status: approved
game: abalone
edition: "Schmidt Spiele German rules, 4 PDF pages"
rulebook: inputs/games/abalone/game_rules.pdf
sha256: c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550
rendered_and_reviewed: 2026-07-17
approved_by_user: 2026-07-17
---
# Approved canonical rule facts
Only the archived PDF above and its fresh renders are game-rule sources. Diagram evidence is explicitly identified. Interface conventions and human decisions are not claims about the printed rules.
## Material and setup
| ID | Page | Direct quote / diagram evidence | Draft expectation | Status |
|---|---:|---|---|---|
| SET-01 | 1 | “Ein Spiel für 2 Spieler” | Exactly two players. | clear |
| SET-02 | 1 | “Setzen Sie die Kugeln wie in Abb. 1 gezeigt in ihre Startpositionen.” | Figure 1 is authoritative setup evidence. | clear |
| SET-03 | 1, Fig. 1 | Visible hex rows contain 5, 6, 7, 8, 9, 8, 7, 6, 5 pits. | Board has exactly 61 playable pits. | clear, diagram |
| SET-04 | 1, Fig. 1 | Dark occupancy is 5 + 6 + 3; light occupancy is 3 + 6 + 5. | Exactly 14 black and 14 white marbles, 28 total, with 33 empty pits. | clear, diagram |
| SET-05 | 1, Fig. 1 | Printed top-to-bottom setup | Canonical row encoding: `BBBBB / BBBBBB / ..BBB.. / ........ / ......... / ........ / ..WWW.. / WWWWWW / WWWWW`. | clear, diagram |
| SET-06 | 1 | “Losen Sie aus, welcher Spieler welche Farbe erhält.” | Color assignment is random/social; the environment may configure it deterministically. | clear |
| TURN-01 | 1 | “Die Spieler sind abwechselnd an der Reihe. Schwarz fängt immer an.” | Black acts first, then turns strictly alternate after every nonterminal move. | clear |
## Ordinary movement
| ID | Page | Direct quote / diagram evidence | Draft expectation | Status |
|---|---:|---|---|---|
| MOVE-01 | 1 | “In ihrem Zug dürfen Sie nur eine ‚Bewegung‘ vornehmen – eigene Kugeln verschieben.” | A turn consists of one atomic movement initiated with the active player’s marbles. Opponent marbles move only as a Sumito consequence. | clear with specific Sumito exception |
| MOVE-02 | 1 | “Eine Bewegung beinhaltet die Entfernung bis zur nächsten Mulde – nicht mehr.” | Every moved marble advances exactly one adjacent pit, never farther. | clear |
| MOVE-03 | 1 | “eine der sechs möglichen Richtungen” | Movement uses one of the hex grid’s six directions. | clear |
| MOVE-04 | 1 | “Eine ‚Bewegung‘ kann eine, zwei oder drei Kugeln umfassen.” | Select exactly 1–3 own marbles; never 4+. | clear |
| MOVE-05 | 1 | “alle in die gleiche Richtung geschoben” | Every selected marble moves in the same direction. | clear |
| MOVE-06 | 1–2, Figs. 2–3 | “Kugelreihe”; inline and side diagrams each show one contiguous straight row. | For a multi-marble move, selected marbles form one contiguous straight row. | clear, text+diagram |
| MOVE-07 | 2, Fig. 2 | “Eine Bewegung in gerader Linie: Die Kugeln werden geradeaus in die nächste Mulde geschoben.” | Inline: movement direction is parallel to the selected row. | clear |
| MOVE-08 | 2, Fig. 3 | “Eine Bewegung zur Seite: Die Kugeln werden seitlich in die nächsten Mulden geschoben.” | Broadside: movement direction is not parallel to the row; all corresponding destination pits must be on-board and empty. | clear, text+diagram |
| MOVE-09 | 1 | “wenn die angrenzende Mulde frei ist” | Ordinary movement requires every destination pit to be empty; Sumito is the later specific exception. | clear by specific-rule precedence |
| MOVE-10 | 1 | “nicht mehr als drei Kugeln einer Farbe” | Moving four or more own marbles in one action is illegal. | clear |
| MOVE-11 | 1 | “eine vorhandene, längere Kugelreihe trennen” | A legal contiguous subset of 1–3 may move from a longer row. | clear |
| MOVE-12 | 2 | “Ist eine Bewegung ausgeführt, kann sie nicht mehr verändert werden.” | Applied movement is final and advances the turn unless it ends the game. | clear |
## Sumito and blocked pushes
| ID | Page | Direct quote / diagram evidence | Draft expectation | Status |
|---|---:|---|---|---|
| SUM-01 | 2 | “die Anzahl Ihrer Kugeln höher ist als die Ihres Gegners” | Inline push requires strict numerical superiority among the effective contiguous groups. | clear |
| SUM-02 | 2, Fig. 4 | “2-zu-1”, “3-zu-1”, “3-zu-2” | Legal strength patterns are 2v1, 3v1, and 3v2. | clear, diagram |
| SUM-03 | 2 | “Durch eine Bewegung in gerader Linie.” | Opponent marbles may be pushed only inline, never broadside. | clear |
| SUM-04 | 3 | “in direkt aneinander grenzenden Mulden” | Attackers and defenders must be directly adjacent, with no gap. | clear |
| SUM-05 | 3 | “hinter der oder den angegriffenen Kugeln eine freie Mulde” | An on-board push requires the pit immediately behind the defenders to be empty. | clear |
| SUM-06 | 3, Fig. 5 no. 1 | “hier hinter der weißen Gruppe keine freie Mulde ist” | A push is illegal when another marble blocks the defenders. | clear |
| SUM-07 | 3, Fig. 5 no. 2 | “hier eine leere Mulde zwischen Schwarz und Weiß ist” | A push across a gap is illegal. | clear |
| SUM-08 | 3, Fig. 5 no. 3 | “hier die Kugeln nicht in einer geraden Linie liegen” | A non-collinear push is illegal. | clear |
| SUM-09 | 3 | “muss er nicht ausgeführt werden” | A legal Sumito is optional; another legal movement may be chosen. | clear |
## Patt, ejection, and terminal result
| ID | Page | Direct quote / diagram evidence | Draft expectation | Status |
|---|---:|---|---|---|
| PATT-01 | 3, Fig. 6 | “1-zu-1”, “2-zu-2”, “3-zu-3” | Equal groups cannot push each other inline. | clear |
| PATT-02 | 4 | “Ein 4-zu-3 … entspricht … einem 3-zu-3 Patt.” | More than three supporting marbles add no strength; 4+v3 is unpushable. | clear |
| PATT-03 | 4 | “so dass sie sich nicht gegenseitig wegschieben dürfen” | Patt forbids the equal inline push, not an otherwise legal withdrawal or broadside move. | clear |
| PATT-04 | 4 | “Angriff über eine andere Gerade … in einem anderen Winkel” | A crossing-angle Sumito may break the local Patt. | clear |
| OUT-01 | 4 | “Eine Kugel ist aus dem Spiel, wenn sie aus dem Spielfeld hinaus auf den Rand geschoben wird.” | A defender pushed beyond the playable board is removed. | clear |
| OUT-02 | 4, Fig. 8 | “Schwarz kann Weiß hinausschieben.” | The rim/outside-board is the specific edge exception to the on-board free-pit requirement. | clear, diagram |
| END-01 | 1, 4 | “Der Spieler, der zuerst sechs Kugeln des Gegners hinaus geschoben hat, gewinnt das Spiel!” | The game becomes terminal immediately when a player ejects the opponent’s sixth marble. | clear |
| END-02 | 4 | no draw, repetition, or other ending rule is provided | No draw/repetition terminal result is hard-scored. | not specified |
## Optional clock rule
| ID | Page | Direct quote | Draft expectation | Status |
|---|---:|---|---|---|
| CLOCK-01 | 4 | “kann jedem Spieler eine bestimmte Spielzeit zugeteilt werden” | Timed play is optional. Clock mechanics and timeout result are absent, so clocks are excluded from the core environment unless the user adds a convention. | not_testable |
## Proposed BoardBench interface conventions
- Use axial hex coordinates internally; publish the exact mapping from Figure 1. Coordinate names and action serialization are evaluator conventions, not rule facts.
- `Game()` creates the two-player Figure-1 setup with Black as current player; an optional seed/config may assign human player identities to colors.
- Legal action names identify selected own cells and one of six directions. Group ordering is canonicalized so one physical move appears once.
- Nonterminal returns are `[0, 0]`; terminal returns are `+1` for the winner and `-1` for the loser.
- No voluntary pass is legal while at least one movement exists.
- **Human decision 2026-07-17:** if and only if a player has no legal movement, expose one forced pass that advances the turn. This source gap is reported separately from clear-rule evidence.
- **Human decision 2026-07-17:** timed play is excluded; no clock or timeout outcome is implemented or scored.
- **Human approval 2026-07-17:** Figure-derived contiguous group geometry, ordinary empty destinations, Sumito’s occupied-destination exception, and edge ejection are hard expectations.
- Exact setup inventory, all ordinary move geometries, Sumito boundaries, ejection, and sixth-ejection victory require hard scenarios.
## Unresolved but intentionally unscored
- The PDF gives no draw or repetition rule. The core environment has no additional draw terminal condition.
- Clock mechanics and timeout outcomes are outside scope.
## Not hard-testable through the minimal public API unless an adapter can construct/observe state
- arbitrary rare Sumito, blocked-push, Patt, and fifth-ejection fixtures;
- physical marble inventory if the implementation exposes no semantic board observation;
- social color lottery;
- clock expiration and draw/repetition outcomes absent from the source.
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
%PDF-1.4
%�쏢
%%Invocation: gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dCompatibilityLevel=1.4 -dColorConversionStrategy=/LeaveColorUnchanged -dDownsampleMonoImages=true -dDownsampleGrayImages=true -dDownsampleColorImages=true -dAutoFilterColorImages=true
%%+ -dAutoFilterGrayImages=true -dColorImageFilter=/FlateEncode -dGrayImageFilter=/FlateEncode -dCompressFonts=true -dColorImageResolution=100 -dGrayImageResolution=100 -dMonoImageResolution=100 -dNOPAUSE -dQUIET -dBATCH ? ? ?
5 0 obj
<</Length 6 0 R/Filter /FlateDecode>>
stream
x�t�[��H����8+(Kq�m��H�`���������dQ$�̔W���w�����O�~?������?����5翜����_�Y���O�������������������I���������Nf�~Rޚ�|��%�m��i�y��S�}?[Q[�i��D���dF����\�O��J�'�ǁeG��)؁S|1|?�� ��9�Uzp�����S}T?�����]NP�k��5����e�s�fa���o� �
ŀ��/��w ��X�gl	N�v���u��;,�7�R�����W��/����H��,o�A����5#���=XVpRQ[���?;X�>!,�Ilgm'�I��⛤�O*�I$�b��~A��~�7��#����5+�;~�r`Q�IEd	L\�s�B���|;_]}�"�{#�6�g�fqW�U����(�q;�$��([d�4�5×=Xv���&��=�c�òHW��y�Ëㄽ��M?eШ��j�C"�T���\�H�[�[�P���`�1 ;��)�%��B�J�1,����y�Ë�#�x�ϭO�,4+���&a;�5,-���5�ſ�`�1 KM��|��BI�1,����y�Ë�m9���ɰ|����	;�R�[������V,�������C����4>?: �z:�e��G����ŉZr�D]�x���B�2�����\�Z��D�e�.��5���=Xv�RS�=}���b�;�e�"�m����q¦��a'~��g$�Nܱn��;�+���-����ϚE��&��Vj"�����E�>��cXkz���(Nԫ�IԪR����֔�θ�%��^]�`d�.��5���O����6<��(�aY�4;o{xq�}Ի���F�`�Y���R	[���z��G�~V��r��O`k��g4&���c�4�j�X�a���1;�e���X8o{xq��m��;��M�߭Y�v<�#��,�z�0��ԁo���1pC�r� Rj"�>��8f�,�����I���$-�mHҮ���֬T�IЁo���y�T2P{ܖ�,��ӫXt�R�F�r�@Ў Q�l[��Nٗ�Nδ�Rr��7l�p�k�Jr���f�APpC���xD �x"Z�*޲�ڲ݃�����wܥ��:�ha���l}���D��	�f%Y�m~n�$��& �G��z�7��,�3ਉ�����~���2�"��p�v�J�$������~]"���9���q�?�����-�s}���"I�b���c���H�྄��2�~t˂�,��=�8�6�dX}�h���@۬3Z�5EKQ������<J�2X3Z��,�]Yy��`�&2E��Ɍ��1,��?\Z8o{xq���Ot���Պ?�V��wkV�w\�0-~��a�&�������S,;F�J��#N@;�D����I���IZFawf��S���o����wsD�g���%���ki� ��=S�c���ہe� (5uu�����3�Mǰ,��8k;xQ��i�ۨxj����5��>�M�	�m,��-��B�^�}���Ƀe� +5�ꍻ��*�aY��>��^'��҄M�i,�K��}�2�'���_${�m����5�+M������Vj"St��$=9�E�"�m���Eq������a��Z22�feڣ��01��W�|V��e��xZ�o�كe� +5�*z���PR��ò`1@!�m/��^}6~ha�6l�v�j��IX>w�%z3�-3ۖ�AH)rtNq�Ӂe� kڷ:���a|=,O.Y8k;xQ���N|��݈�ZmC�ЬLyF��o�ҽ�O�2P[0Z������`�1�JM��+��aY����i����Qg�Q٨wkA#7�D6�Fy�"��%���OM��Z��ˎ���x�v�l�g��8�e���X8o{xq���j���Ԣ��5+Ռ�X��!��;�DWS��-�D3ך�8҃e� l�`F}�(h~2�e����p����8`�L7{3wC�c�˛`�Y�&��������3�|o��?kjrtc����c ��H=rzX(tˀE��y�Ë�]M�fؑi�6��;�Ɠ7�$�HqW�D8�&�)����h��;Y,;`��T�#������шe���X8o{xq���e���z7����n�J�B70 ���c2�P)v=�MF�;��@�"�D����=a�,�<'m/��t�����"Rh"Qb�^����ږ��Ƴ49��9�`&�Do��/���X&ofZ8c{x��+�f�N�kSƻb�ЮLNܧG��c= ʁyO��I����Xv���>�'���1 +�e���@9�������%��H�X��&NhV�#>WĈ�inx�!�����ARjr4�=Xv� �&2�ؠ|�!�e���X8m9xQ���.��$���wkV�S�y}�W<�Zgor���#���CM��`�ۃe� (5��9{X3z�a9H�Ŷp����8Qk���~�x��n�J�q*�b<w�T5�3�"�����&G�3��`�1 �4Y8��j�yᗤ��ʶp����8a�����K�)b�J�ƏA2@ܐI�B�Ԋq^ir4���,;P��DW�� �w��e�])��़�f��͐ѵ18'�W�ZbN�1	�N(��`�\��#�ꅃ�����~�oN���;�CY�����y�Ë�M�iy��~�1
��+SL� 
In�G	�$�5s ��-�1��
T*"Qt��  s����#,��=�'i�@^m��ӆ��T�<'�W���^�v�q��O�����h/��=XV�RyfܧI��S�"�c���8Ik������_+V�7'�����=`䛷-e�r؛����8��*M��^��A����F�,���B9�����C�ƫ'���8�Yy^���3B_muA0���-��B^�������#����3F�� �	a�7;s�p���8Qo/�YhtoԘR��ĸy��(>�	H�n1P��9 ir�\���ֶzь����jq�B�h����(�{N�'����ݚ���y�9�Z[�eo�:�m�&�C7r`�!�JM]e̐�C�I��"�E�b4Q��^'j��5N�S_��֬L;��#�{�V^i��ϟđ�yu=�B�㉋g�ܲ ����q: �0�e����p�����oR�"���&�:��o���K�9��I����"�è?,;`��T������aY�-��=�8N�՝aC}��Ш
���R�/���H��e�b�����8���c ��H5�4t�1�v��Ŋń�p�r�8Qc6���w�ѭ�*4%�u̎G�#~��i`�"@�P����gQ8;N��S�H��V�Rт_�#Xh�:JY8i{xA��׭I�e7�(I�ݚ��JЄ��	y��C��Tdܤ��[t �RyNܫ��+M��a �ŊBY8g;x1��H�[M���K�j@3�w2Iс)Xջ�|HQibK��m��ہDG )�'��yy�����H�'m/���i�7���^�Ӣ1���CbK2#�x8S&�Td�f�ܲ���ٚ�����z�,N���9����,Is����X�	djJ��1�,Z��r�%��m^W~P�8�����7���.�O��g�ċVN�^ɟ����7:Uat��]xL���H�Nkr(�DƜB���h���N5z�� ��v˂�p����8a����e��~�(1��͜ϓK0�ު[��6���"1kG���D�������!�\���+e_}���R�m{M��Q&��c���1*\r9`04krv%ٹ�#kIٍ�;���)M�`�\�ռXez�2�~��_��#��[Sb 㕫c|�JLsǔA��˦&Z��`�1@�Հ��;�C֯�1,��dZ8o{xq������|�`��֔��酰�H��$R�	�VMZP�qa�,;X��L3�QMI0�BX*��d���Eq��QˏҸE��t��0����,�w��8jr\�Uf�`�!@JM$}/y���k�Zn�BES_��N�4F:ё�Ѳ�ݚ���IԘ�����fh�M��/Z�f�&�`g����c ���4|�@�!Q�#�;i_��8Iwc!~r�F���e����s�� �.*e`&6��ɱ�$�}�e &5���}��^��D(�e�����ؗ��1���c��o�߭)X���~k����� ��ؗ���_y{��Az�US�t���Ҹ��1,��Ŷp����8a[�q溋0�������S�ѧ�<��Q��w+9�.��/��  �&�L�K/�9���H1c,'m/���t���\���Q^j
>�DR�`W�����X��uL.g�&�Z���`�1 KM�]|y�1��.~�
,ʂ-,��=�8N�44?sax��{��5%>�Y��rs`BJ"X�)H�cY|t���C����4�3t�c +u��H�E��I���	zM/��,�mȳ��*���{&�ȏL�-����ܲ ��H3�dc�
Kt�ݲ(����������K̩wF��&�$#�A6�[���%��ZIvl��&�,}J[�w0��d��uyL�qR�,�w1-��=�N�65=���kՍ�[W�V�x��V��b�4i��ʴ	��=���Vjj�B{ �|bXk��c���Eq��M)���diJ�C����?�>�l�+]�ɱ������c,Pk"Op�A�����,N,��Ӗ��ə��8�b�z����'�+����,P�2P�s�,���$Ht���*��ty��9��a ��*vY8i{xA�����sj�(O�� v &�b�t�K����J�jIP�H�φ,;X��e�k��(����ITY8o{xq�mzgq��ӈ9/�rD,���+��ZWG���ϨY(�����c ��H}pz�1��'�e�򻦅��	۽�x5��<c���֔xvp2�{yu@��<�#���05�$s5Xv�RS;ޥ7�o[�ڜ[~)�Q�q�+��zoq��m�������l43��Lܨ˚����1iA���K�{�A^	��� ����B�ǔ�������S���mǒ�߭(�lL��X#x�mw��?��;�ns7>y�� �5R������?���!,�Ke���8Ioo(�q����rh��qz�gV&�eV��9�IM�V˵>,+BpJYF�Rr���z��,N,S��r��ᠬ{�Ua�t��Gq�عA�6��6k�oV��(�RK��Y��L�=XF 0R����Z�����"�[�����?���0(~M-�߭)��Ϻ/�6�G��Ʒ)e 66�Y�����C���H3|�âh\�����gm/��z�pl�4J5& ��oDŠ���?��]���^�-�faT���� ����5�s[�1�anA��ϟ��/���;�c�X�T׫�beɭ0��Üv�kqz�D�b*!��3Z�в=/���}��<ǂB���"r� dw�J���O�ۛ����H5*�)�F�6�Xh�Ć�]�8�28�_�A	{��@MZ9�Cr,MO�B�A�m/��L�.?�U�ɰ_g�6�������.\�@�I�\$s��؃e� ,5�j����`�7cX,���y�Ë���S+���.�QAM�W'�����.lJ$v�J,KJ���e�v`�!�U��-!8X ��o��P�4�����ŉZ��6 O��:�Լ~��6�THX�]�I)*�X�@0� �]��:Fh� Ǌn6E2�>���t.�����ŉ�7h,��'�]�����y!����17g($ic�'iH����C ��ڱ� ����f (u<��^�Az�U�]���o���o|E���qo��$iwȁe� i�:��>7�]�[A)l'��_'���Z�F��ȓ�{�E��3�$F�}n��Ok���X� ���D��u�C��%X|������p����8`���-�9�65��L������H[l��"iJ��<Xv�&pG�< ��ò`�|,��=�8N��]�5��MN.OAM����s_�B�9�y��d�rdI�����`�1 {i	�`��iX��tcX,�T��y�Ëㄭ�Essx��.RA�J�h�{}v�dL���<b��d�r�P���nt;���*M�A7]�c;��0�e����)��W�'d���X��h�:�4�nBvP�^�z�J�}�b!�y��%: ;W"�h��j `�,�[co��S����yy�0�x�H[©)�r�Mc�t%�2m7��Ig�p�4��u!���D�1�(9s S!$
+�5���}�� M��icx��+~s�[��5�=1�FUw�B�hh�D��-9o��`ߝ�Kt `��<��n*�ԫ�������$8e;x!���;ik��Xs)Nh
�����r��)qa�Z"(/Q�bAdܽ�ڢ݃2kmf�B���q��[&_��p�r��oJ��I����)�0�>�(M��i/������X76Ɂe� )5�(������8������Y����D-�-\Yw(�������>���Qt�.ۅ����:O�,Nkȃe� ��b�/nѪBO]�sòX��m/�6y�p��%R`vt�"@�HQm�E@v~�P�+/�l��(Md_���-�	#X#����򿹟t���k)~�i�*5%Z�S��x��h@w���dPr�P���z����&�D��{]�rò0��m/���!\�O���^�z�e�Z(�f����� ��l�,)ہe� +5�)���5�����r�6Б����ŉڼK8>��4&���ݚ�)*�!L,}Kz�E�OK�D�M)JT�j��Nj"MLv�A���C ����]8e;x!���ۄ��aS�	���X׃_VC�\2@3�Y����`�!@JM$:q�fr��a�BţJ��N�TM����P��5%:S��n��0K�]ؓa�\*���zly�� �IVN�``�cX(���y�Ë�D��Ixu<���~SS�3�U+L���׋3N��>5������^ؖe9j��cXl독���R�+m�Et�Q,4+��Y�5���&k�]�}Y+�=I�/n������D��W{���������p���8Q�w
���Ku)
jJ�1��.ȩq�&�x�`-�?kjb� ����c V�$K��PP��1,��e����q��n�H��(�F��w�Rj��.�s�؁J�,���qz����&Rq��C��XX����q"[8o{xq��ɛ��"����S�REuN�A��U�B���[+�=I�@
��޲# ��M롒�CUr�ݢ(��8a\���D��K��>шZ�q E����n܆�C�W��*�`lddm���H�Xv0�@�H��A��n�a��䝬�8��^Q;�i��YA�nM�^r�O��L,ʶ�}�@e�'iɍ�qy��`�&R͸OU�i� �BH*���Nڗ� N�]-2���.GA�ʳr��qaNj{ȱ��m�8$��Ł>�HtpByV�ry*D``�0X(���I���$-�'ܚ�k�}�w+J�dr�2�]&�޸���ٹ�&_��������&~��=���8`Y��S����L�8۴+0�`��V�^S�F_?�x
��]�g%���ؤYh�z��Hȑ� �6�ơˀLƗ������/MG�6���jPP��d;$b`��rX�]7�SI����j�:�y��ढr͘�kp²@S{,��=�i,eU�~�ݓT������ݸ�,��CfQ-�fź�أ1�Ֆ��TD��}��Š�8�oQ���&����������nן�,Yx`��^JZ��8�0o9@3W�H�@XA\,;P��L�aK9J�bYCX*���i����D��ee*��F�u1�9��͕��(�v��O�ɧbqܘG��Rj"��'E����F<e�b!�,���(N��}��=��:<�[�2E�a��C�����L|�f�:�,�Mȁe� *5�)f���:M�a�b������ŉ�){#].@E�1��_/���A�����Q� mlMP����<����D�� �pD�zs��%q���BY��	qp�ۥ�����Ԕ��Vo��@� i`h�2P�yӒ�+qQ�<Xv�RSGa<�o6Y�F1,�d����q�vo�-��#���{S�R�����_�y$r�[l��jJ�F>y������3"%�ݩ���CY8o{xq��՛��VX�SgvISbPK�h�E�����Ԍ�4�(t�E )5�g�����sr�#X(ډ2p�v�b8A���vVk#���Ę�~7n�L��/1������Z,�ĥw�`�1�JM��xVY���7�aY�-��=�8N��[h�?����J��o�P0�Aeˀ��܁������`�1 KM��8=�8��~bX,�
��y�Ë�a�b��Űh�Ůr�o��OT@"XqU.oE�QΊ|ݬ�(�"X��L'^�׏�F�,��������Ł;t��t�k�~���&�[a'-�4�:��KԄBC�,����<Xv�RSW�]qzX(�}�����,��=�8N��=ýq�h�5�ZI�����w_㳊2`Y�I���=��`�1 KMռ�<�8��w˂�,��=�8N��m�\��{�b�Ia/���ᓛ�KlgǕ��R1@��C������O �"Ő�,��=� N��Ý�,�ݼ��r�D��3*=���7)�����,��f<�@� ����_N�ƑBy:�Eq�?NY׿N��{�{�/�+~���@%��ǀTP���"=28+�P�0��s�D &�%z�|Q��X��)����\8����Qui
jV�<�'�`��V<L^הb�
/j7�Ƀe� ����x�����`�d��G���	۽c��(�0Ri
jJ�b#xcݍ���#��J3�@�\�����B�b]-��H2ň��q�W��%�9�w���_韌՛�c9D�����bH��M�ԄH3ǔA�~�E��@���C�sh�G�8f�,�4��p�v�8Q�7�K��w��֬L�&�+��ֳq���:�@�T�4��aaHt�ByVܤ�g�s�ؕ�z8�"-�p����8Io��ָ0RU
���T(5�ԅ��"��(T�q�,�����W+e� j�c�I{X$~��&Y��1p�v�8Q���'�(�#	�ڈ���oEʁx�.��\}�v;5�&�y9�c�,�^�kg�^��÷wu�ٻ��!�&���z���ɺN�,��Ue:�H�c ��:zL��A��%k�!,�t���i����D�G먗0�7j�f�<���4iJI=��k�)��NH�@��_,;P/��v��!ǉ�w�1,���Om����q��S�'yƝ\����	��xvbJ��#�Z�X�x�Ŝ��o�c]aM���� �>w˂M��p����8a�y�u��&s��r�<���t�fm����{�
��
O����؃d� �NX�e�h��bXj�c�����8A�Y�ё���[�m�
o�ﮇ��eW����ӎ����]��x��@�&2EG���(�e��{V��m/�6ﳈ��J#� ���
v�7�iR썬L$o���d�Ɂ��@�C��j���� �~;�E��?��^'�>�x�r�C��GQL�pJ�a�Y�qr�Q�f�@M|L�`��U9��@������C��CX�菁���ŉ�wy�k�ި�e����f�ć9�@O����M~,�z_`K�<Hv�R�fܭ�A[��e ��~��_�����W�'�>�xt�e]�JAM��"N��Z^Z�yTb���F�x�Ŝ�ntz��`�t�v��!80ԧ�Ez���y�Ë��G����Ǵa1g��Ɋ��7F���:8������D3��h��)�-����(�eq��X8e{x!�i�>�QcppaMf	ш\�:"�_)���m1#��8�� �"\�N�@��!,��>��N��s<�>^n�,�	�z	MM�w�$���@�-y� �4�-�h�Ƀd� hS'd��M��(����p��pR�����e���Pa
*JL�qR�d��0̑Cg�";�}b�U�NLl�3 +sC�����c[��Ji�w���ϴO�}��來7�SSb���������1n�yI��%; ��4��PDɛ�Wǽ+�4Ū���}��������~�F�K�7�R�48kK��>	�ܱe�V�nd1��EG g�ѷ�7/_,� �A���p����8H�9�3qc��)��rIO���40p%�A�4�"�9��h;�� �&��+5lr�ލbXj~���(N�}��~�0RI
jJ���+���g�$��-U岘1P���d��I�;�6�ՠ�}��,���l/���D9��I�f͕X	5�������e�&������ɎVj�m:X$��;��&Y�-=N[^'�>sx�a�&�[SbB��׋c:c* ?��ڝ��z��7l3�ɎTj"ӄ;��lòX{,��=�8N�}���IKx�	��ב8�ap���@8��{�=YL�@����c V��&�P��1,v���y�Ë�ݧO��CP��X�^�޸O�fU`��G^i�yZ���� �!�JM$�@XG1,��P�vpB��>sx�QW�k�����mkD�IQ//U��TVw�����؃d� �o����1��E��c���Eq���'�g��~��Bb���e��������1oa��%[�0��1��S�Q�a��*�bX+�M�������q��xg�9ϱ�}�F��Zn9>y
�����uˀ�\[����ǃd�Xi0HT���BaeŰ,���m/�v�;����_+�řGA]�h<���c(��l1��1���D��ɑ�`ycXjϏ�����/h���e��:���nM�IjN��Lt�0;UӖ�Z�J����Ƀd� *5����aQŰ,T����y�Ë�`��5��`�{6&��v�\�chF�l'� �J|�}6!��%�=8��l���\ҥ�On���`[8e{x!�����9Y[;f;�	��4c!NV�/6&�3	(�u�l1c�_z<Hv�R��� ,�a˂M�c����q��Æ'wևQ��������<8�+1B����9�X��b6U��ɎXU��c[
+�(�e���X8o{xq��>o8��E�:UHSbb���x><���m}7?�>��G��]hӅ����D�	w�����ٹD�
�ݹ��W�'�ON��G�	�����$�����ЈG�ɵ�#}La�b��Ee� �1�TL���B@�gcX+�p����8`����D҆�嚜�<�'f�ёdˀ���-f�Ћ=Hv�R����=6��Zt˂�p����8a�-��4;�*UHSb��qR\�l�M�28Y�3*ʶ�r� Nj0�(=,
��Q�༟?;c_�"8!}�pq`�R�
i"O0��ѹ�-*�-���f-XIv��]�H0�� ��ùE���C'k��OB0���B�K�ܤu�a��8�s-)��Y$k<�`VB؁d� ���Y���'7���:� I�9�?;e_�B89}�p�Ňչl�wkJ,$���(�"�����a�,�k��Ö��� L(�<������b�,����I��� �>_8�x�0J��;�����;/oR��m� �,��s�*��ˁDG )5�ht��`�ha?CX*����Y�Ë�D���B���C��feZ8�yTW�����S-�Cl��Q�r>$;D�J�F��HXG1,�u<��^'�O�����FE�*4%V�`<�����OQ_3e�r�-f�3�$;X��T;n�{�b��1,�sR�p����8a}�p��k]c�Q�͢���)L$������-f~6��u������IAŰ��a	Y8o{xq���~�buK�~ӏ��|ϊ@<w*�&������U�l1K�2y�������f��ò`�������|�pM�p[8%a
��̹��Jp���2Pq,ö��ڃd� *5�(:�� �2�e���X(k;8!NP���.�R�1�1DJ��A*�2G�X�2Pu^�,f���ۃe� �Q�8=�YG1,5����Y�Ë�m�N�w�Q,5�c$ա,Q�d2���,�������u�E�Ni"Kt�y���a�
`Y��ː������s��(����ڜ���ssxg�0��%���@�B����YЃe� ��ܪu�bU�hK�%t�Ŷp����8a}�p�ڇܱ���QĪ(L�Gџh�U�<�x��e�r��-f�A��`�!�JE,�G7���+�e�f�퐅�����$�I�)�P&�d�R1U�7��S5ǘ^-��9,̿��_��r��L*�� �)+����wDw.���|��AW}�p�4<��n��>dM<�D!�X"��.���l�ځeF �ۭ���A0�m�-�ɟ4���'�6��r��i¾�S-ʈ����Xben�,�d�$�ǃe� '�fŝ�zO%s�BX(���I��Iq��x��6�mԁ;��7f�i\�ҋ'�b���q`Y!�J���μ�e"��bX��9����D�9�I��c��5�qɁ�2��1F��޶�m�{#�e)!H��<��勣j|��#��%�p����8I}�p���T9Zؿ�&V�aR<���.ĸ��e��4DY����`Y1�JM��
�(�D����Nї� ��3x�W��a��G�۰-�s�8�	�l_�W�-����.�G$>$*8p�=q^�ce ���X8E{xA��>�7V�f�QI������h�G��<�P�{��L���-�]\ܚ�3�s�>֠rj�,�~Y8C;x1��>~7V_7�n�R3��;E��@ɚ���>�/��&�Τ\�����맥��k���_���~���l�l��~M�����}�q�P4%kc%��+�de�K7����b�2i����M@A��1,�����Y�Ë���±4���[�)����%"� 
��D"�W�F;z���-fb{������c���^3�e�b��,��=�8N�k��z���SX3G�xt��ZXȮ6VG��$XZ�X�P�#`����7�P~ӥ�(�bX,���Y�Ë��>g8��Ҧ��X��-�q@.�ElC��K{{�6[̛%���B uhaMgǻiLaUŰ����P�vpB��>c8���n�R�1�r�%�BE˥u���R�|�Ō9��8�� mZ\���`a�&�BX��)���	�#��(z�1��7h�wzs���F���$���Q�m�ϛ;Au�E�dՀV �z@`!-X%��p���B89}�pl��J�e)��e�� �+�����D08H�(�b�y�|r;��`�&2E��G/�����P�ZP��^'��N1I�wS���S�ޕs�n���#�ٹ�A����
 ʤ$YlH�j�0�eab��,��/����|���Kh���f���1��� R������ܲ���ʒ8��� �p���g(/���G�.�Tit�7*M,C�7Kp�Vآo�U���7�؃e�Ti"St��a��HcX+Kj��Y�Ëㄭ&��O���M�X��9ój�G�Vp� EI�m1/V��ˊR��gp{���P���.�BN�l�,��=�8NR/�|�?F��m͌� l�$��j����x��sNe�n�Tځe� +5�iԓ���QR�Ĩ�<%����(NT�/�R�lz�BO�R��,zo|K��%2��)L�	
m1�zx��`�ZH6�������ư,����Y�Ë〽}�p�>�Q�>�X]�I��M�wj,�ְ�V"X�+��b1.;��`�Zu��Q�a�`g7#Hhߊ���~!��>Z8���N�[����bl�mǎ��YfC2@Q����j����B����4�^E������R�7�r���^'���y�6pkf�6�8у�f�NĘe�[��
O����q
y��`�4L0QA_
���a�]w�����^'��R��Q,5�������כ�y�fc�2X�Xi1V��\/Q���&:�|aL������'h/����Gm��~M,��$���Vs�آwU���Y
Y�ɲ�`Y1�ڵ���P�0�1,�5���Y�Ë〽|�p9��a�*���}�.L˱)��m1&�v Q�
E䉎8/ϥ�L�K'Z������/��g�4Ԍ���mh����zw���R&7B�b�4A}<XV�R�L�/��TU(�1,��gY8K{xq��>u8
�������G��9޹B0�'u&��V�x����9�� �PD����:9�oQ�X('h/�����Q�4ʛ34��m������)ϡ�P�8l����ۃe� *5�j�ޑ���:9�aY�ؐ*gi/��gG	*�Gy�J3[����2A���40x}�@�ʓt��1qH���(��Fu�}=(F�,�sp��,��=��r��Y�����#�,�5�.>�b�QL�)l]�T�ǒ����q`Y!�U���µT�\���P�DI��^'�N�K�FRU
)bM<��5�r�Z'{0�zq��,����,+H�A�lܩW�T��a�B�l�,���'��v��X��EJ�lIs�<��^].����,.9P3�=�b�vx��@�&2ҬzO��aY�폅���ŉ��i��",aۤ��[�����ˀ�*�e�>�e1)ڃe� )5�h���Q�ư,T�̴p����8Y}(oT:�ˈlc ����_(.�,�~�2HY��cpQ�=X��qZDu��K�j=U.�U ���|Y8E{�Kp0�śb�A\�J!y֩9��A����^8����2�1�9��TD��[���*�S�6�5r�ĶP�vp �7%��q|�Ģ����"v_r�6�@��28�8u���$�=XfpRi��,
��}��t���������$�q�Q�4���JD�l����\���{�2PY����n�=XV�`�&��@/<��S��W �Ĳ������OF�2F�_6#3d���K[ʪZ𗷔��������B ���p8
.Ʃn���8]���p�v�8Q}�0��N]B�&6r4�b�~K)�ߣR��������� Rj"Qt�����e���JxZ8G{xQ��>n8�"'|���hbK���H8�U+KJ��D�bt�tكe� ,5�*��Y���|bX�?���������j�x��Qڰ��]�>��f�"����SG��L/�I����Fi�����ܥ��7mC��:�.��s��ŉ��x�.��]�*��5q?x<��=��+kS���l��)�@�"���3z��|q�b�K'֤75���/��>�7
�cB>6ip"Q����y�1_Z��k�4�X^�m��в\���Q�(/ �0�ݲ�6PN�^韌>�7��?F�f�h/��c����y���OF���d1��B29���JE�	��Y��r9:�\�@�@�P^'�����X�ύ��f�=E@pآV�_ ���d��X��,+@�^����2OM�ròP�c���E�ߨ��(m����b�h�,P�"A�G�Y�WJ�gB�8d�+�<f��ײ�����_�x��8���M��Ħl��*�8齳�Z�e��b4<��ˊPj"հ���R~�!��߿;E_��8I}�0ƸiTD�I����H�:2QP?(p��½P2:^�,+@��cc.J�j� �E�b����(NT5FXhЫ
QX��0��:��B�I�ŻS+-F��)�ˊVj"��gެ�aY��������	�vB���K��P���G� ����G�ѷ�ĭ�1�3����(lm����us���H�c���Eq��������[���+Q�}-�e�R�����m�l{o�#X��T��N�����<�#�����Y�Ë〭>l8��b�3�w+b�f�y�������G�+��"��B2y��@�&EǛH�r���+�)�m�$���8A}�p�Ô3��H��D1>X%�꨻�4j�r�ެ�d�8����`Y1����L�V�U���ȩ��@Y�lW��I����D�A�a����]�B��P����������g�vג���1��۱�L,+���5qxr� �8��,�T�O�p�v�8Q}�0�W��]��hf��|$�^9Yx�E�v�� �4�1<;��������Uo-k�������2p�v�8Q}�p*�q�$R(b��M΢c@� U�Y�q�X,@��ٚH3�C� ��[�;�e�b��,���f�Q�aÏ�v)
i��}G��ͺ��&�e�V��i�{�?,+���58�<�� ��İ,��8G;xQ����F�]i�r��ƹ����w�2����k�q�ƶE]Zy�����D��|k�G骍���}�����^'�����9���.͌�퓰<��6D"h/P,<�"����2y�����D���*��Y$�!$
�,��S��/���G�j�˵)������oq</�}�v+�Cgb=(��^��r�
��lM���t �1�e�f�U��S���I�s��RLt,��}4�eǂ��C��s�D0�B�,�d�8�3��`Y1����T���N]r²XQZFNR^j���Im��?66jhf,]Di�G�o(�(�d�V��-+���5�g��z��pUBXhy��}������)
4�����2��^8�	�,0�1@/��Ŀ����Z��?VD��_*��U'�h/x߅r[8?{x��>x8N�ϲ�x�����:x���X-��C� �1�"�LƂ}y��w�k"U���a��RCHj��}��$���am���6��-ƭ5� ��Ү�i'&��x����ִ�oTz 	V�0�e�b9�,��=�8NX�fk�&lT�B���/���dT�G�#��m1�e�,*���5�g���Al�����M0}��?-�h/��4�����%Qd]���.PL���:8����e�V���"�vF9�����4͘��"�3�1,�5=��^'�O#,��}��/O׉(<����D��2X5�+�8]Ooy�����D��j٬���ŊJ$�p����8a}�p�L�oq�M�����݇qf2�{
&%5��#�8\����2#|?[y�?N�C�r
g�.�3�}QN�N�����ď�����[��&&*�OK��Iw�:Y�������ي�3�*W���0�e�b�BN�N�����C��R�ĥp	�	�40xD�X6h�8iC�r`����h���)�v��a ��,�����Sx�zZ�Np%�oQ0K4��)R��^�"���f?y�����D��2Kr�Uyǰ,V�g�"��(zxq��>�7�dS7+Pf��ǁ�|�%��)�,Z��ΏE�����ٚH3��r�0T$�!,T%�e���D81��o������Ln�B`�Y�s%t�@D�*דɁe��~�&���<��?1,�4?��^��:Q�-�f�8�43]�	�	8P�����t����������`Y1����Tc3�<,��a�b�2AY8K{xq��>m8��F�.64O¢S��/XW�\sˀm��EN���<XV��gk"�����B�; a��:򿝜/|�2����p�Yl?�D�"�1�DB".<Y,�}� dq'[���x����ִ�K�!(�ͳh+���b[(I;8!��g�ƳZva
i�͚����[�#0�x�&k;�"�,<XV��gk����R8����q}Y8K{xq��>k8y>��Ϳ�����	���k��e��� ǭ�ǁ�'���L�Rv��N�P�N2PyH�-Ҟ���ŉ�#�S�(N�Жpib�����VmPcx�B(K=��q�e������ٚȳ�U���r9Yu�.����S���I��èO�M�yn
M$��������z���l���ٚH5,�a��\CHꟿ;E_��8I}�pj��T�B�Qo$�����<Q/n� �tz$�h��ǁe��~����?_
,с���3J�JW���Y��M���_�,�X-���/r�-b�dX���DG��Ֆ���ٚvs�,U�ɜ��P��2I8A;x!���ژ��pD�q,c"�����ß�{�$�T#���y������XiƁ:�|aV����DY�X+�h/��G�8V?�8ŕ��Lθ°��jH�GY&��i���N���ˊ��lM���� ��vˀU�^Y8K{xq��y�f�y�(WÆ&v�sR\��QE���UW�����"N���L,+���5�j�a�a��jcX,e�,���q�޳�y��"���>�H���]��D$��W���2�������ٚ�4�g:�e�f#X*�Q�p�v�8Pǜz�r�7꜈��($ŚA�EX�C�{������`Y1���i7�s�HP]�1,��e�,���q���R0,:u�b�4��﬌�tS�̥e�f�6�f5�*���ٚH5�͂�7�aY�(I"gi/�v��t�v����9�*M[�OK�2Fi�@M��iG%`'��� ���D���}�*���E�2p�v�b8A��V'��p�
iPiͤ�%�	sd+ՊO���ƭ�he�����ٚƓ��a��zcX��2BY8K{xq����Ҏ69V�KVH3Y7aЋI��sa��2`/NUɢ����`Y1����T;�׋�MS5tò`�ϑ�������q4�_�[�*M��HDŸX�}Qs�:tʁ�y��-P�;o��ٚ��񮓹�J�0�e�bhM��^/��*F����I�M�!� xs�Q�Y���h[ǘ�����s�e��~��݉]r:X������Qg�c���$8)�U9�on۩��*��<�A�+���E+�Aڱ�EQY��q`Y!����D�#���Q�\�,{Pe���Eq��˿]5�k��pi�|6�ǩ��P�����'����Ɨ�,:O��,+���5�j���(Cg˂,��=�8N�4��B۵zk�4����=qW�h˚��N���Q�g��j�r��lM�Cl�eɦ
�dM`�]@gh�,��=�N����{�'���������f��ZX�-ߜB�Ԣ�7-���?�ˊ��lM�:p��
�d��ԩ�3K�(E_��8HW�PU�#���&ʄpr|r6->��40L��e�L����ٚ/\]���,�4���_'f���Ue���G%B�/<:���3)fʪE@j���bS8�\�[�{��5-V\E��kF����0Q���ʔ�=� N�zi�k�zR��f��P��^�D^��R�N��E&��ǁe��~�&2�x���T�ư,��8G;xQ��>�7����1p��h�
��'ʻ�����F��Xi��.��`Y1���i,�m@imǰ,��gi/������ʨ!Xj�N��0��1�C�o��ڸ�W�" .�(�ߏ�e����\/��QQ�˕s�vj�����8�mv�ʈ��"ʠ`>|�,�8�)���)�ǚO6��`���يH3>9 �,�`10��6p�vp2��#NI'�l�\�9qz�9>/cĝ85�(�e�v���flC�$2��c��E��63ٿea���,��=�'f�*g�`u�e�3)P��.���4�U���;��ͭ�>,3����'��t�8�6V�"EypY8I{8)N�r_�J�^�!'Ũ����%���ipf��fk,�d�������r�_�r��`��X���.G)��_����L��p"��cp|^�:'���I����B��ˊ��lM䉎�<�K�rC�Hy�Z�����������h�+j�4�b4j�&��4���oY��{���}�RE�[�z9�!Y���)gi/�v���HEñaCUm�)|jU��|I��[l�Vuƾ��x�����D�wjڰX����,l�,���q¶����qa�rT���ND�z�h�0,�Л���{����ܲ�?[�n,���Ŧ�#H'���B��IpR�k򁤍Eat�$��Trbt�֙��(��՚lkï?,+���5�):��Pu��cHj�������	��/�X��a�`E7���o4�W�QQ�:��F����˃e��~�&RE�[�O?Ɛ,�z?��^'�5oݬ<W(�T�B�͓�l7w+��9&�`e�&[`�b�,*���5�(��rP]VJ!�.+�$l���Eq�F�J�k�
�p�
�)X2!�޹�ܩ�i���jg-,Y�§X/c���ٚH�oyL(�da���,_U��o�'`_�d�J.S!M�+����	�HKR(�	Sk���l���ٚ�3Vw���>�w�����!-��=�8N�������$�T�B����������N\iz�ʲM�����x����ִ#��C�x�cH,�������	����J�VqiP�)�ߪ[(��e���A�����v`Y!����L11.A��9�!Y��1p�v�8Q��Ό&i�HE+��*M��G�䝇��`�f�!�"��p��<XV��gk"Ut���,w}bH+���������T�f��P{�4���&
5a^<�{p��(J�޶X�p�EW%9{�����D���Tl���!$�����I����D��4���vi�a!jR�DE�oܜ����u�@��O1�<����b|?[���C�`��bH+ڍ�p����8aWSR'�#���]\��Y#�`i~��Ԗ�2`�â���HT��Ǌvc�ƾ�����e���p����8Ic'�IQ7$V�n҉۵pV|b�'Ο��&m(h,�.�E���4t9�����D���C�a��ĐV$a�h/�5�Z���3�T�B�")O�hܯ�Ҹ�R�t�Ag	].I�+"�h%��`�(+�Kc�c��t�+���ާϋ+�K�VqiFO��Z[��u������-�䟣��7]mY�����,c���z:�OI�8�vv����	�O���śĥ��b���z����Z���ؒ�E��^{�����D���C�y�cHk폅����	�O��A���>�(4�M�G�F�~�h���'=E[y��y맘����b|?[��7.��5:�!Y�y������	���<n<�Z�v�4�M��j�OusI��pRa)'����s�e��~��EY��߾��*�#���V�j�(9{x�2�S�gbE�����G3T�$O>��=
��Z�B���E<b��=XV��gk"�}��@��ŐXfagi/��Z}I=���A(���h����Ov?��=�).���K��c��ˊ��lM����<�[�tC�`ӣ�Y�Ë��S]�4*64#��݄E};�DߴS���|��|^����b|?[�6ܪ� ��!Y�8nD��^'l��>=���jWP��0>��/j��guk�'e�����"ʁ�â�
��lM$:p����>�C�Pْ��������V8Lm�*���}4QJ�����#1���@e9'[D=�H�,+���5����Jq�b�J1$�=���=�8N�|�fX�ގ
64�eΊO������6kE�,�"x�n���ٚ���*�J�2Ő,X����Y�ËㄽF�7۰� u�KM���~q���3n�n>1�E��r������ٚ�3~��X���AZ�?;?_�"��]I�i�4n�\���(�W�X�\/V�Cw�NVs�E�˾����B|?[��?.��-��!����J�N���F�A�>n��f��*~�Qw����܄:T-GZo���ٚ�=~�]S�*�d��G�����	[���xN���4#����(�_yo䑷TVt�AԒƪ9�����D���F�!Q�8�O��^'i���o��y��`!M��xe)��j@ѹs�`�Q㲈��1a���ٚ�XX�b$	�uC�`�gi/�����o�29�Q,5�5�_+g"Б�[k�ZCYD��#��
��lMd��=`44=1$�u<��^��=�|]��n��G1�IЩR�شx�D)�4��6-P��q`�����4������H��c���$8)��Ӕ��C�ŭ<�ra�(����Q�� ���=\�s�e�~�&�D�\0/�'�dp2[8E{xA��u}�7��g}'(Q�s�<�4�,��<��2P/ʤE�|�.�@�a�=����i�Y�S,��=�ɟ��y�	�X�u�d}�Ԍ��>I�����RoNh�V{(T��er`Y!����Dc,\b�kdA�HKy,���(N��A���[.7խ�&
=r^\G�j��̱��Jퟋ%���cEÐؾ8�7`��K"f.d��t�+����1�ef�z�v�[59%�X�*��Q�o�A�CdU[����ٚ�S��P�*�(�d�b-�,��=�8N��2+vog�濏fDi�AVLB��7�+qg����9��XD��{>,+���5�)z��5WO�"�<��}����w���g4�~MԳ�����)�G�x�@�����~k�C�[V��gk��w�A,��.E�Ю�-��=� N�r%}�Ur�D5KΉw=^/��.��/�RLEdZD5S,3�ˊ��lM��R96F.�X�#N�NR^'j��IQ�;��&JYrZ��JW摢�_Q�vOȢs��`Y1����D1-.���o�B��AY8K{xq���}�osl��}4�4M�s3d�3�2��g�H,k��"*|bE�<XV��gk�Jt��+��C�`�Q������ۆ���6�Dn�R�;9-޹�07��D���2N�{T��:3]oY����D3nW8���Sf�����/~��M�������RD�N�����M!�kn���"�^�?,+���5�(����cЖV�"ň�,���'h�j�r/\��BPjFɚױ癭, [���c�/�?,+���5�(����=C2Hu��,��=�8N֬�ęew2`ڰ���`3 -�y�T$�ږ;��ұUO�ˊ��lM�l{�}lX������,��=�8N�[���5w"U�S�&�WG~f�c]:1){+��ZDMHL�ȃe��~�&����C�7ň�bH�_gi/���(�7���
RDQV·�8H��8��w5M�`�L{,�J"V�ɁeE�~��h �Cp���!Y��1P���D81���v�e�U�(�K�X9���,p�R��V��$ޏˊ��lMd�q����m�!Y�X:(gi/��pEs��6Y��D�YΊs'd��:�(��E���� �bI�XV��gk����CUen��(R,�u�o�h/��t�y��M\ϗ�WX�g97��Q����"����RN6@���q`Y!����L�����<\$u���9����D��^��)�|�z�5#F��T��T"
�]8b�2PWC�"��a�C,+���5�*����W�NG1$�Y��Y�Ëㄽ.��ui�t4�R�v�	�y��tc|%�V�o=���(��Uf�ڲ�?[m|<�n=�TVG$�����/���p>&LPp6M��&��rf|r�`��D�&� )[�%LZD�9�����b|?[�����>1$����Y�Ë�D��P�c�I�Q,5#�^�����T���,�H���P[D�9���ˊ��lM��,��"f�!Y��+������	���8�^$2T�()�Ɋ��7��bK�2Xu��,��V�сEE�~�&E�\��U�������p���8Q��g��Q�F�\�[�+�ڱ~eַ����[��a@,+���5�it�� @�Z�$�Ke�u������8�,IF�@����1��Lّ��O�i�_J��sT�h<�o{�����D����(h�C��Y��Y�Ë��>�7sMe��>����~A�a����WRaL3�D�2�����B|?[#J��A�`Ɏ"Hj�c���Eq���0B���U�(�����׏D��2P�ϣ@�2,���
��lMd�^9�R���@���ߝ��~!�����g�@Q�r�݊��w]��1�����].�v���-��ڃ���~5�(��tŧ�TG!$�4e�u������Ⱉ2�.qkFb{$b`��j����� M*����Q���ˊ��lM$��D����JŐ,����Y�Ëㄽ��8ߓ�'	-��G��c#�����`��2`U;UQ�
;5���b|?[��W.QkuC�`�C��^l��e�'��KV��f�fW���*���\?c�`�Xv]Q�
Op9������`>:��#�!�Z�%�h/��i�q�&oR�t�"� 񑎚s�+�:��ETv�
9�����`�">;y��(δ���|���X��8'�Z�s:� ���ر(1B�M�<S���o�܄hv����b|?[�b8C⌙h�9�d���/gi/�6i�q��/�FlJ��[&+kCaI-��Ә2XQ��Q�	�\9����VD������l�X�� �ʧ3-���'��řU�`�̉�����!��J!,T�|�U�,�d<����ي��� 8b��!$�c��p��pR����cOx�e��b` b`�Ê�����,� �,��QL�ɁE�~��qg��>N0��#H'Fe���d89ۘ՜�ȝ�v�[տ���V�r�[da��=J aZ]�Z���gkb���� N��'�dP>�NΗ��?�T��h��#5�f��\��bG�����Ep様Rg�,��
��l���!.A��!��\�$�h/�5kSqf�8�
�&Tj��yD�WȲ��_LO��:N���8�q Q�+"O����qh�O �"�w,�h/��4iwqNn�&հ�&*��J�m�i\[��G��q���W[���gk"Kl���:�v�,����	���伴�8�Ƒ�tk��5Q�<F#�A<�S�sU�K���d�(3���"��;�W���u<�%7�,����t�I����S��A$���P�e�L��B�	LP�W�����!����v:���n��Sȉ��C<]^=���ɠy:��#P7�G�V�&�~&G9Ӳ4�޿lX6�����b�ڝS�A,ȍГ*9l��)w�P��qH&Փg��R*Lr��m��g"�Eb��L�c��y2T�#�a�8�D����q�Y�Ts�������Ti�L�:��Rѫ{��U�Z�R��\��5���LH$U������Ebe�oY���9M<�Y�y+G>�l��'����F�����6��3���#+蝁��o�$���{����Jrsq�/.l��yԬ�.�l.�r��u��d��
@��_"����D�)k [�_6,�k�ψx/�d���̡�}R�� pu�E���g����3���j���,��5D������U9YC�*��M���/���c%{8��;����
���l�Tv�Ӫj�I&�a�����6�~&����o|��&�?�F��hx�XɦOqE�M�9]����1m�F��*X^0�R2��.�G��m+�l?Q��T _$��5��������a�׺�vQ9�=�����"z[��Ց��~��SF�ŗ�ȶ��3��Pk蝁ӆe�t��G��hx�XɦE1��a���AЄ���בE,�!�#�+)�d���(AQ�GAd����<�A���u>,�*#c=">F���B�L��Z]$�����A�M�Q0�*l�����Ƞz��SF�0C4D�����\��zW~elX6�� ��hx�XɦM1]�M�����KT98��u��5eR=u�z�P���&�~&G���~���ذl���;+��hsRq�J�D0�0S!��i(J����<�����L3uJSy�(�l?A���� _&$�甧���Ea�;��V��eЭvɌ��"�`$u8g����#�~��SF�j��!�m��L����>T('6,��2�����lq>1�VS�\�%v�O�bu��#�M�d��;N�,[Cd����\�Z��P��ذL��"#�e4�x,d�k�~/�zT��σ�
���X^ޞ�D~6���9e�����ȶ��3��4xk ��>6,�,�2="^FË�J�tNqUS.R��D.�ь��fK]�$���sӳ�,��)��d���j}�XNLX6WN*<"NZ���J�;����Q���B��g�]!Cq7�<2���� �eV0e�����\
����؂e3m_#�c�X�T���+��������j`���PyN6���L�E+>�@�w��G*��4�l6>��,�%i��͓�.��Ea�Y�T\��Xt�|!��qx�a�R9�ǔI�S�@64�ʬa�e��1W�$��>��h�a�d9���x/+�,�륪ܥ:U|"W��x׹�P36��\2���\5b�aS������S���U͉	˦�3)���V�b�0���ksd�=h� 
���(E=���M�,��#�=)-��)����D�)��� &�ˆeru��G��hx�X�'c�s#�p�%rU�;�_���=k�>g�]·��-��)����D�*�@����IlX6��zF��hx�X�֤���ul�|!׮s�d�t{AWG�6�P��F����aʲ��3��5���a�d���2^<V����힧��O�����?�Dsk�eS$׮�+�� �ˬ`�2��3xJ�R��wL��S_Z�s���/+�m+!�-����`�Z9S���ޮ��d�|�k��\=E����|��\_Uˉr�f��	��w����±_I.n���A�I9/��Y;#ᇲ��2�RO�;��N�̪�F�$�<k*�ݖ�Qoe��s�������6�B{�����/��>c��S`��Fk�U�)#`QS����	�O&�Z�2|�لe2�'�ae�mI.n_��Z�ƺh� �kɀ���IӻO�XE.*�`�eK�j�"dg	_�YC��&�?H����+���M�?�}�� �s�8�\��ҳ)�O�V�Y��*����a�|NX��W����-��x\��c�|�|%�%�����zD��>D���M55Ъ�1��IrÎ������0e����<���0��v�mX6��5"^FË�B�^�9��}g�^�d����o��s���U%�,&�3��1ʣaʲ��3N�\Z/\�چe�e8�G��hx�Xɺ=q���ƞ.����R??��?����d�T���`e��h����L>r�m��P۰l����\���ʯ'}��8��p� EN~N�M�t�mi츊�F�6gy4LY6�~&?Y����֊H6,���Ȉx/+��G��'��u*�,��!�?&ޝ��`�J˹=���H�۾LY&�~&G�m�K�1�mX6�����be�����őbA�M�.O�����6eR�*L�HGcؘLQ�~&��GS�0�&,�)#=">FË�B��%qņ�1.U�|��zzf]�uzf�#���`���h��l��L�V>�Ҁ���zlX6�� ��hx�X��%q�?�,���T�r��������ʦ-���	��J���X-��)����D�*3֬T���&ˀ�����ⱒMKbb�t��!Ke�}3D��/Q:����<1��j�᱆)����D�*W�ր]m}�eò�2H�#�e4�x�dӖ�v�[O͊ ���p�ٮy��H�2���$01�����w
[Showing lines 1-90 of 1995 (50.0KB limit). Use offset=91 to continue.]
Read image file [image/jpeg]
Read image file [image/jpeg]
Read image file [image/jpeg]
Read image file [image/jpeg]
grep: implementation.py
grep: implementation.py
grep: canonical_rulefacts.md
implementation.py-44-     @staticmethod
implementation.py-45-     def current_player(state: GameState):
implementation.py:46:         return None if Game.is_terminal(state) else state.player
implementation.py-47- 
implementation.py-48-     @staticmethod
implementation.py-62- 
implementation.py-63-     @staticmethod
implementation.py:64:     def legal_actions(state: GameState) -> Tuple[Action, ...]:
implementation.py-65-         if Game.is_terminal(state):
implementation.py-66-             return ()
implementation.py-63-     @staticmethod
implementation.py-64-     def legal_actions(state: GameState) -> Tuple[Action, ...]:
implementation.py:65:         if Game.is_terminal(state):
implementation.py-66-             return ()
implementation.py-67-         occupied = {(q, r): colour for q, r, colour in state.board}
implementation.py-96-                     if all(_inside(c) and c not in occupied for c in targets):
implementation.py-97-                         actions.append(("move", group, i))
implementation.py:98:         return tuple(sorted(actions))
implementation.py-99- 
implementation.py-100-     @staticmethod
implementation.py-99- 
implementation.py-100-     @staticmethod
implementation.py:101:     def apply_action(state: GameState, action: Action) -> GameState:
implementation.py-102-         if action not in Game.legal_actions(state):
implementation.py-103-             raise ValueError("illegal action")
implementation.py-179- 
implementation.py-180- 
implementation.py:181: if __name__ == "__main__":
implementation.py-182-     game = Game()
implementation.py-183-     state = game.initial_state()
implementation.py-183-     state = game.initial_state()
implementation.py-184-     actions = game.legal_actions(state)
implementation.py:185:     assert len(state.board) == 28 and actions
implementation.py-186-     assert all(game.name_to_action(game.action_to_name(a)) == a for a in actions)
implementation.py-187- 
implementation.py-33- 
implementation.py-34-     @staticmethod
implementation.py:35:     def initial_state() -> GameState:
implementation.py-36-         board = []
implementation.py-37-         # Figure 1: five, six, then the central three on each opposing side.
implementation.py-36-         board = []
implementation.py-37-         # Figure 1: five, six, then the central three on each opposing side.
implementation.py:38:         for r, qs in ((-4, range(0, 5)), (-3, range(-1, 5)), (-2, range(0, 3))):
implementation.py-39-             board.extend((q, r, 0) for q in qs)
implementation.py-40-         for r, qs in ((4, range(-4, 1)), (3, range(-4, 2)), (2, range(-2, 1))):
implementation.py-38-         for r, qs in ((-4, range(0, 5)), (-3, range(-1, 5)), (-2, range(0, 3))):
implementation.py-39-             board.extend((q, r, 0) for q in qs)
implementation.py:40:         for r, qs in ((4, range(-4, 1)), (3, range(-4, 2)), (2, range(-2, 1))):
implementation.py-41-             board.extend((q, r, 1) for q in qs)
implementation.py-42-         return GameState(tuple(sorted(board)))
implementation.py-47- 
implementation.py-48-     @staticmethod
implementation.py:49:     def _groups(state: GameState):
implementation.py-50-         occupied = {(q, r): colour for q, r, colour in state.board}
implementation.py-51-         own = {c for c, colour in occupied.items() if colour == state.player}
implementation.py-90-                             count += 1
implementation.py-91-                             cursor = _add(cursor, direction)
implementation.py:92:                         if count < len(group) and (not _inside(cursor) or cursor not in occupied):
implementation.py-93-                             actions.append(("move", group, i))
implementation.py-94-                 else:  # Bewegung zur Seite: every adjacent hollow must be free.
implementation.py-94-                 else:  # Bewegung zur Seite: every adjacent hollow must be free.
implementation.py-95-                     targets = [_add(c, direction) for c in group]
implementation.py:96:                     if all(_inside(c) and c not in occupied for c in targets):
implementation.py-97-                         actions.append(("move", group, i))
implementation.py-98-         return tuple(sorted(actions))
implementation.py-133- 
implementation.py-134-     @staticmethod
implementation.py:135:     def is_terminal(state: GameState) -> bool:
implementation.py-136-         return state.ejected[0] >= 6 or state.ejected[1] >= 6
implementation.py-137- 
implementation.py-137- 
implementation.py-138-     @staticmethod
implementation.py:139:     def returns(state: GameState) -> Tuple[int, int]:
implementation.py-140-         if not Game.is_terminal(state):
implementation.py-141-             return (0, 0)
canonical_rulefacts.md-82- - Nonterminal returns are `[0, 0]`; terminal returns are `+1` for the winner and `-1` for the loser.
canonical_rulefacts.md:83: - No voluntary pass is legal while at least one movement exists.
canonical_rulefacts.md-84- - **Human decision 2026-07-17:** if and only if a player has no legal movement, expose one forced pass that advances the turn. This source gap is reported separately from clear-rule evidence.
canonical_rulefacts.md-83- - No voluntary pass is legal while at least one movement exists.
canonical_rulefacts.md:84: - **Human decision 2026-07-17:** if and only if a player has no legal movement, expose one forced pass that advances the turn. This source gap is reported separately from clear-rule evidence.
canonical_rulefacts.md-85- - **Human decision 2026-07-17:** timed play is excluded; no clock or timeout outcome is implemented or scored.
canonical_rulefacts.md-86- - **Human approval 2026-07-17:** Figure-derived contiguous group geometry, ordinary empty destinations, Sumito’s occupied-destination exception, and edge ejection are hard expectations.
canonical_rulefacts.md:87: - Exact setup inventory, all ordinary move geometries, Sumito boundaries, ejection, and sixth-ejection victory require hard scenarios.
canonical_rulefacts.md-88- 
# Abalone rules review
## Severity-ranked findings
### Major — Forced pass is missing
- **Fact ID:** Approved convention `FORCED-PASS` (unnumbered)
- **Evidence type:** Approved human decision; rulebook source gap
- **Page:** N/A
- **Direct quote:** “if and only if a player has no legal movement, expose one forced pass that advances the turn.”
- **Code:** `implementation.py:64-98`, `101-103`
- **Expected:** A nonterminal player with no movement receives exactly one forced-pass action; applying it changes the player.
- **Actual:** `legal_actions()` returns `()`. Consequently every action is rejected by `apply_action()`, while `current_player()` still identifies the blocked player.
- **Impact:** Such a state cannot progress. Whether it is reachable from canonical play is not established by supplied evidence, but constructed states are observably noncompliant.
No other critical or major rule defect was identified.
## Rule-area coverage
| Area | Result | Implementation evidence |
|---|---|---|
| Setup / 61-pit geometry | Covered | `_inside()` radius-4 hex; `initial_state()` encodes 14 marbles per color and Figure-1 rows (`:14-16`, `35-42`). |
| Black first / alternation | Covered | Default `player=0`; successful moves set `1 - state.player` (`:29`, `132`). |
| Ordinary movement | Covered | Contiguous groups of 1–3, six directions, inline and broadside destination checks (`:49-98`). |
| Sumito | Covered | Inline-only opponent handling, strict superiority, clear space or edge required (`:84-93`, `113-126`). |
| Patt / blocked pushes | Covered | Equal or stronger defender groups fail `count < len(group)`; groups never exceed three (`:49-61`, `92`). |
| Ejection | Covered | Edge defender removed and per-color ejection count incremented (`:119-126`). |
| Sixth-ejection result | Covered | Terminal at six; winner returns are color-correct (`:135-144`). |
| Draws / clock | Covered by omission | No unsupported repetition, draw, clock, or timeout rule added. |
| Forced pass | **Missing** | Empty movement set remains empty instead of exposing pass (`:64-98`). |
## Missing deterministic tests
The only self-check verifies 28 occupied entries, at least one initial action, and action-name round trips (`implementation.py:181-186`). Missing hard checks include:
1. Exact 61-pit geometry and Figure-1 row encoding/color inventory.
2. Black first and strict alternation.
3. Single, 2/3-marble inline, 2/3-marble broadside, and splitting a longer row.
4. Rejection of four-marble, noncontiguous, nonstraight, occupied-destination, and off-board ordinary moves.
5. Legal 2v1, 3v1, and 3v2 Sumito.
6. Rejection of 1v1, 2v2, 3v3, blocker, gap, non-collinear, and broadside pushes.
7. Edge ejection, fifth-ejection nonterminal state, and immediate sixth-ejection result.
8. Exactly one forced pass when no movement exists, and no pass otherwise.
## Questions
- Are arbitrary `GameState` fixtures part of the supported public API? The supplied facts anticipate constructed rare-state fixtures, but do not specify validation behavior for malformed boards, colors, duplicate cells, or inconsistent ejection counts.
- Is a no-movement nonterminal state reachable from the canonical setup? Evidence is insufficient; this affects practical severity but not the explicit forced-pass convention.
## Score / confidence
- **Rules correctness:** 9/10
- **Deterministic verification:** 3/10
- **Overall:** 8/10
- **Confidence:** High for static rule-path review; medium for rare-state behavior because no scenarios were executed.
The requested artifact was not directly written because the controlling review instruction forbids file edits; this response contains the complete artifact content.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Reviewed only canonical_rulebook.pdf, canonical-page-1.jpg through canonical-page-4.jpg, canonical_rulefacts.md, and implementation.py; no files were modified and scope was not widened."
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "Finding includes approved-fact evidence, code locations, expected and actual behavior, coverage, missing tests, questions, and score/confidence."
    }
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "Read canonical rulebook, four canonical page renders, approved rule facts, and implementation",
      "result": "passed",
      "summary": "All supplied review inputs were inspected."
    },
    {
      "command": "Search implementation and rule facts for relevant definitions and evidence locations",
      "result": "passed",
      "summary": "Located setup, legal-action, Sumito, terminal, self-check, and forced-pass evidence."
    }
  ],
  "validationOutput": [
    "Static review found one major interface-convention defect: missing forced pass.",
    "No critical defects found.",
    "No runtime tests were executed because no command-execution tool was available."
  ],
  "residualRisks": [
    "Rare-state behavior was not exercised by deterministic scenarios.",
    "Reachability of a nonterminal no-movement state is unresolved.",
    "Malformed GameState validation requirements are unspecified."
  ],
  "noStagedFiles": true,
  "diffSummary": "No implementation diff; review-only task.",
  "reviewFindings": [
    "major: implementation.py:64-103 - a nonterminal player with no movement receives no forced-pass action and cannot advance."
  ],
  "manualNotes": "No files were edited or staged by this reviewer. The artifact path was not directly written because the controlling instructions explicitly require review-only/no-edit behavior."
}
```
[38;2;136;136;136m✻ Turn took 1m 38s (Total time 1m 37s · 1 turn)[0m
