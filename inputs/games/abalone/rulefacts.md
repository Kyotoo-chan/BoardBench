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
