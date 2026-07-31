# 6 nimmt! V2 scenario matrix

Status: **approved**

- Atomic claims: 42
- Required material/testable publisher-clear claims: 30
- Planned scenario groups: 33
- Component-only expectations remain human-decision-basis.

| ID | Basis | Cases | Fact IDs | Title |
|---|---|---:|---|---|
| `6N-R01-2p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 2-player setup |
| `6N-R02-3p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 3-player setup |
| `6N-R03-4p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 4-player setup |
| `6N-R04-5p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 5-player setup |
| `6N-R05-6p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 6-player setup |
| `6N-R06-7p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 7-player setup |
| `6N-R07-8p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 8-player setup |
| `6N-R08-9p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 9-player setup |
| `6N-R09-10p-setup` | clear | 1 | `6N-C-PLAYER-RANGE`, `6N-C-CARD-TOTAL`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` | 10-player setup |
| `6N-R10A-supported-count-initial-play` | clear | 9 | `6N-C-PLAYER-RANGE`, `6N-C-FACE-DOWN-COMMIT` | Initial legal play for every supported count |
| `6N-R10B-supported-count-bounded-play` | clear | 9 | `6N-C-PLAYER-RANGE`, `6N-C-TEN-ROUNDS`, `6N-C-GAME-END` | Bounded game playability for every supported count |
| `6N-R10-player-range-rejection` | human_decision | 4 | `6N-M-INVALID-PLAYERS` | Reject unsupported player counts |
| `6N-R11-card-inventory` | human_decision | 1 | `6N-M-CARD-IDENTITIES`, `6N-M-BULL-INVENTORY` | Exact augmented card inventory |
| `6N-R12-hidden-joint-reveal` | clear | 2 | `6N-C-FACE-DOWN-COMMIT`, `6N-C-JOINT-REVEAL` | Hidden commits and joint reveal |
| `6N-R13-private-seat-protocol` | human_decision | 2 | `6N-M-COMMIT-PROTOCOL` | Irrevocable seat-ordered commits |
| `6N-R14-ascending-resolution` | clear | 2 | `6N-C-ASCENDING-RESOLUTION` | Ascending resolution order |
| `6N-R15-minimum-difference-example` | clear | 1 | `6N-C-ROW-ASCENDING`, `6N-C-MIN-DIFFERENCE` | Mandatory minimum difference |
| `6N-R16-sixth-card-capture` | clear | 2 | `6N-C-ROW-MAX-FIVE`, `6N-C-FULL-CAPTURE`, `6N-C-SIXTH-STARTER` | Sixth card captures five |
| `6N-R17-low-card-free-choice` | clear | 4 | `6N-C-LOW-CHOOSE-ROW`, `6N-C-LOW-STARTER` | Low card permits any row |
| `6N-R18-low-choice-pending` | human_decision | 2 | `6N-M-LOW-PENDING` | Ordered resolution pauses for low choice |
| `6N-R19-dynamic-3-then-9` | clear | 1 | `6N-C-DYNAMIC-RESOLUTION`, `6N-C-LOW-CHOOSE-ROW` | Dynamic low-card recomputation |
| `6N-R20-dynamic-adverse-cascade` | clear | 1 | `6N-C-DYNAMIC-RESOLUTION`, `6N-C-FULL-CAPTURE` | Dynamic later sixth-card cascade |
| `6N-R21-capture-zone` | clear | 2 | `6N-C-CAPTURE-FACE-DOWN`, `6N-C-CAPTURE-NOT-HAND`, `6N-C-BULLS-ARE-POINTS` | Captured cards leave play |
| `6N-R22A-publisher-scoring-categories` | clear | 4 | `6N-C-BULLS-ARE-POINTS`, `6N-C-FIVE-SCORE`, `6N-C-TEN-SCORE`, `6N-C-DOUBLE-SCORE`, `6N-C-55-SCORE` | Publisher scoring categories |
| `6N-R22B-component-bull-inventory` | human_decision | 2 | `6N-M-BULL-INVENTORY` | Complete observed bullhead inventory |
| `6N-R23-ten-round-boundary` | clear | 2 | `6N-C-TEN-ROUNDS`, `6N-C-GAME-END`, `6N-C-GAME-SCORE` | Exactly ten rounds per game |
| `6N-R24-new-game-reset` | clear | 1 | `6N-C-NEW-GAME`, `6N-C-SHUFFLE`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-GAME-SCORE` | New game begins below threshold |
| `6N-R25-threshold-strictness` | clear | 2 | `6N-C-MATCH-THRESHOLD`, `6N-C-GAME-SCORE` | Strictly greater than 66 after game |
| `6N-R26-lowest-total-wins` | clear | 2 | `6N-C-WINNER-MINIMUM` | Lowest cumulative score wins |
| `6N-R27-shared-winners` | human_decision | 2 | `6N-M-TIE-WINNER` | Tied minimum creates co-winners |
| `6N-R28-seeded-reset` | human_decision | 3 | `6N-M-RNG-RESET` | Seeded shuffle and full-deck reset |
| `6N-R29-observation-privacy` | human_decision | 3 | `6N-M-OBSERVATION` | Player-specific private observations |
| `6N-R30-return-contract` | human_decision | 2 | `6N-M-RETURNS`, `6N-M-TIE-WINNER` | Terminal returns |

## Approval meaning

Approval freezes scope, decisions, claims and planned expectations only. Executable scenarios and adapter are built and reviewed afterward; no generation or evaluation starts without a separate GO.
