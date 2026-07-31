# 6 nimmt! V2 rule facts

Status: **approved**

## Source condition

- `6NIMMT-V23-RULES`: AMIGO publisher rulebook Version 2.3, PDF pages 1–2, SHA-256 `b200ae0558c283ba86f331037402d9150675958ac6a6dc3e5df188435626539d`.
- `6NIMMT-V2-COMPONENTS`: separately attributed user observation, SHA-256 `01e8f5dbe0cdca5ea514e628da3e5ed71ceb17729bbd22ac3a309c44cb2da950`.
- Scope: base game for 2–10 players, full default match over 66; professional and optional target/count variants excluded.
- No publisher companion is assigned.

## Approved decisions

See `decisions_v2.json`: one copy each 1–104 and bullhead inventory; full match; private seat-ordered commitments; shared winners; strict seeded runtime/reset; hidden opponent hands and captured identities; pending low-card row choice; terminal returns +1/-1.

## Atomic inventory

| ID | Class | Material/testable | Expectation |
|---|---|---|---|
| `6N-C-PLAYER-RANGE` | clear | yes/yes | Exactly 2 through 10 players are source-supported. |
| `6N-C-CARD-TOTAL` | clear | yes/yes | The physical deck contains exactly 104 cards. |
| `6N-M-CARD-IDENTITIES` | missing | yes/yes | The publisher does not enumerate identities; the approved user observation supplies one copy of every integer value 1 through 104. |
| `6N-M-BULL-INVENTORY` | missing | yes/yes | The publisher gives special categories but no exhaustive ordinary-card map; the approved user observation supplies the complete bullhead inventory. |
| `6N-C-SHUFFLE` | clear | yes/yes | All 104 cards are shuffled at the start of each game. |
| `6N-C-DEAL-TEN` | clear | yes/yes | Each player receives exactly ten hand cards. |
| `6N-C-FOUR-ROWS` | clear | yes/yes | The next four cards start four public rows, one card per row. |
| `6N-C-ROW-MAX-FIVE` | clear | yes/yes | A row contains at most five cards before a sixth-card capture. |
| `6N-C-RESERVE-COUNT` | clear | yes/yes | With P players the reserve contains 100-10P cards and is unused for the current game. |
| `6N-C-FACE-DOWN-COMMIT` | clear | yes/yes | Each player commits one hand card face down per round. |
| `6N-C-JOINT-REVEAL` | clear | yes/yes | No committed identity is revealed until all players have committed, then all are revealed together. |
| `6N-C-ASCENDING-RESOLUTION` | clear | yes/yes | Revealed cards resolve in strictly ascending value order. |
| `6N-C-ROW-ASCENDING` | clear | yes/yes | Ordinary placement appends only to a row ending below the played card. |
| `6N-C-MIN-DIFFERENCE` | clear | yes/yes | Among eligible rows, placement uses the row end with the smallest positive difference. |
| `6N-C-FULL-CAPTURE` | clear | yes/yes | A sixth-card placement captures exactly the five existing cards in the forced row. |
| `6N-C-SIXTH-STARTER` | clear | yes/yes | The played sixth card is not captured and becomes the sole new row starter. |
| `6N-C-LOW-CHOOSE-ROW` | clear | yes/yes | A card lower than every row end forces its owner to choose any one of the four rows and capture all cards in it. |
| `6N-C-LOW-STARTER` | clear | yes/yes | The low card becomes the sole starter of the chosen row. |
| `6N-C-DYNAMIC-RESOLUTION` | clear | yes/yes | Every later revealed card is placed against rows updated by all earlier resolved cards. |
| `6N-C-TIP-NONBINDING` | clear | no/no | Choosing the lowest-point row is advice, not a mandatory rule. |
| `6N-C-CAPTURE-FACE-DOWN` | clear | yes/yes | Captured cards enter the owner's face-down bull pile. |
| `6N-C-CAPTURE-NOT-HAND` | clear | yes/yes | Captured cards never enter the hand and cannot be played. |
| `6N-C-BULLS-ARE-POINTS` | clear | yes/yes | Captured cards contribute their printed bullhead counts as penalty points. |
| `6N-C-FIVE-SCORE` | clear | yes/yes | Other multiples of five are worth two bullheads. |
| `6N-C-TEN-SCORE` | clear | yes/yes | Multiples of ten are worth three bullheads. |
| `6N-C-DOUBLE-SCORE` | clear | yes/yes | Repeated-digit values are worth five bullheads except 55. |
| `6N-C-55-SCORE` | clear | yes/yes | Card 55 is worth exactly seven bullheads. |
| `6N-C-TEN-ROUNDS` | clear | yes/yes | Each game has exactly ten card-selection rounds. |
| `6N-C-GAME-END` | clear | yes/yes | A game ends only after every hand is empty. |
| `6N-C-GAME-SCORE` | clear | yes/yes | At game end each player's captured bullheads are added to the cumulative score. |
| `6N-C-NEW-GAME` | clear | yes/yes | If the match has not ended, a new fully set-up game begins. |
| `6N-C-MATCH-THRESHOLD` | clear | yes/yes | The match ends after a completed game if at least one cumulative score is strictly greater than 66; exactly 66 continues. |
| `6N-C-WINNER-MINIMUM` | clear | yes/yes | At match end the lowest cumulative bullhead total wins. |
| `6N-C-ALTERNATE-TARGET` | clear | no/yes | Players may agree on another target or game count, but this condition uses the printed default. |
| `6N-M-COMMIT-PROTOCOL` | missing | yes/yes | The source requires simultaneous hidden choice but not a digital submission order or undo protocol. |
| `6N-M-TIE-WINNER` | missing | yes/yes | The source gives no tie-break when several players share the minimum. |
| `6N-M-RNG-RESET` | missing | yes/yes | The source gives no seed, shuffle algorithm or explicit digital reset lifecycle. |
| `6N-M-INVALID-PLAYERS` | missing | yes/yes | The source gives no digital rejection or exception behavior outside the supported range. |
| `6N-M-OBSERVATION` | missing | yes/yes | The source does not fully define player-specific digital observations for hands, commits and captured piles. |
| `6N-M-LOW-PENDING` | missing | yes/yes | The source does not define a digital pending phase for row choice during ordered resolution. |
| `6N-M-RETURNS` | missing | yes/yes | The source does not define numeric environment returns. |
| `6N-A-TEN-PLAYER-REST` | ambiguous | no/yes | At ten players arithmetic leaves an empty reserve although the prose refers to a remaining stack. |

## Coverage plan

- 42 claims: 1 ambiguous, 32 clear, 9 missing
- 30 material, testable clear claims; all map to at least one planned hard scenario.
- 33 scenario groups: 24 clear, 9 human-decision, 74 planned named cases.
- Every supported player count 2–10 receives setup, inventory, initial legal action and bounded-playability checks; unsupported-count rejection is explicitly human-decision-basis.
- Claim mapping is not complete assertion coverage; the executable suite remains to be built and reviewed after approval.

## Remaining unresolved material questions

None. The matrix was approved on 2026-07-31; executable expectations remain evaluator-only.
