Score: **0.90**, confidence: **high**. The movement, pushing, turn, pass, ejection, terminal, return, and public-observation rules are substantially implemented correctly. The principal defect is a materially incorrect initial setup: each player receives 13 marbles instead of 14.

## Findings

### Major — Initial setup omits one marble from each six-marble row

- Canonical facts: `ABAL-C-SETUP-FIGURE`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS`
- Evidence type: `rule_quote`
- Source: `ABALONE-RULES-SCHMIDT-4P`
- Locator: PDF page 1, Figure 1
- Exact evidence: “Setzen Sie die Kugeln wie in Abb. 1 gezeigt in ihre Startpositionen.” The approved Figure-1 transcription is `BBBBB / BBBBBB / ..BBB.. / empty / empty / empty / ..WWW.. / WWWWWW / WWWWW`, totaling 14 black, 14 white, and 33 empty pits.
- Conflicting code symbol: `Game.initial_state`, especially `range(-1, 4)` for black row `r=-3` and `range(-3, 2)` for white row `r=3`.
- Expected: Each second home row contains six marbles, producing 14 marbles per color.
- Implemented: Both ranges contain five coordinates. Combined with the five- and three-marble rows, the initial state has 13 black, 13 white, and 35 empty pits.
- Impact: Every game begins from a materially incorrect position and inventory. The game can still terminate, so this is major rather than critical.

### Question — No draw or repetition outcome

- Canonical fact: `ABAL-G-DRAW`
- Evidence type: `rule_quote`
- Source: `ABALONE-RULES-SCHMIDT-4P`
- Locator: PDF page 4
- Evidence: No draw, repetition, or move-limit rule is provided; the only printed terminal condition is that the first player to eject six opposing marbles wins.
- Code behavior: The module continues indefinitely until a sixth ejection.
- Assessment: This is not a contradiction and is not scored as a defect. A human decision would be required to add any repetition or move-limit outcome.

No critical or minor findings were identified.

## Rule-area coverage

| Rule area | Result | Relevant claims |
|---|---|---|
| Two-player configuration | Conforms | `ABAL-C-PLAYERS` |
| Board geometry | Conforms: axial radius-four board has 61 cells | `ABAL-C-BOARD-61` |
| Initial placement/inventory | **Major defect: 13 per color** | `ABAL-C-SETUP-FIGURE`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` |
| Player/color mapping and first turn | Conforms to approved decision: player 0 is black and starts | `ABAL-C-TURN-ORDER`, `ABAL-G-PLAYER-MAPPING` |
| One-step, six-direction movement | Conforms | `ABAL-C-ONE-MOVE`, `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` |
| Group size, shape, subsets | Conforms | `ABAL-C-GROUP-SIZE`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-MAX-THREE`, `ABAL-C-SUBSET-LONG-ROW` |
| Inline and broadside movement | Conforms, including all broadside destinations being on-board and empty | `ABAL-C-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION`, `ABAL-G-BROADSIDE-DESTINATIONS` |
| Sumito strength and geometry | Conforms for 2v1, 3v1, and 3v2; equal, gapped, blocked, and non-collinear pushes are rejected | `ABAL-C-SUMITO-*`, `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-FOUR-THREE` |
| Patt alternatives/crossing attack | Legal withdrawals, broadsides, and separately aligned stronger pushes remain available | `ABAL-C-PATT-WITHDRAW`, `ABAL-C-PATT-CROSSING` |
| Forced pass | Conforms to approved decision: exactly one pass only when no move exists | `ABAL-G-PASS` |
| Ejection and sixth-ejection victory | Conforms; terminal is immediate and winner remains current player | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SIXTH-WINS`, `ABAL-G-TERMINAL-API` |
| Returns | Conforms: `[0,0]` nonterminal and winner/loser `+1/-1` terminal | `ABAL-G-RETURNS` |
| Action uniqueness/serialization | Generated groups use a canonical orientation; no generated physical-move aliases found | `ABAL-G-ACTION-UNIQUE` |
| Public information | Required board, turn, captures, terminal, winner, phase, and move number are exposed | `ABAL-G-PUBLIC-STATE` |
| Chance/private information | No gameplay chance or private information; deterministic ID/color convention is appropriate | `ABAL-C-COLOR-LOTTERY`, `ABAL-G-PLAYER-MAPPING` |
| Clock/draw rules | Clock correctly excluded; draw behavior remains unspecified | `ABAL-C-CLOCK-OPTIONAL`, `ABAL-G-CLOCK`, `ABAL-G-DRAW` |

## Missing deterministic scenarios

Scenario artifacts were outside the permitted review scope, so their actual presence could not be inspected. The deterministic suite should include or add:

1. Exact initial row strings and the `14/14/33` inventory assertion; this directly detects the identified defect.
2. Inventory conservation after ordinary moves and pushes: board marbles plus captures remain 14 per original color.
3. All three legal Sumito patterns at both an interior location and the edge.
4. Rejection of 1v1, 2v2, 3v3, 4v3, blocked-behind, gapped, and crossing/non-collinear pseudo-pushes.
5. Broadside rejection when any destination is occupied or off-board.
6. Forced pass as the sole legal action when no movement exists, plus rejection of voluntary pass otherwise.
7. Fifth versus sixth ejection, checking terminal timing, winner, retained current player, empty terminal action list, and returns.
8. Action serialization round-trips and uniqueness for single, inline, broadside, and Sumito movements.

## Material questions for a human

- Should repetition, a move limit, or another draw mechanism exist? The supplied rulebook does not decide this (`ABAL-G-DRAW`).
- Should imported serialized states be required to enforce inventory and terminal-field consistency? The approved public-state decision specifies exposed fields but not strict cross-field validation.

```text
score: 0.90
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```