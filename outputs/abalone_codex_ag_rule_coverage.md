# Rule coverage

Only the four supplied German rulebook pages are game-rule evidence. The
contract/profile supply representation details only.

| Source section / named example | Implementing symbol | Source-only probe or reason | Assumption |
|---|---|---|---|
| Ziel des Spieles | `Game.apply_action`, `Game.is_terminal`, `Game.returns` | Probe: sixth opposing marble pushed off makes the mover the winner and removes legal actions. | None |
| Vorbereitung / Abbildung 1 | `Game.initial_state`, `CELLS` | Probe: 61 holes, 14 black and 14 white marbles. | A-01 |
| Der Spielablauf: alternating turns; black starts | `initial_state`, `apply_action` | Probe: initial player 0/black; legal move changes player. | None |
| One movement per turn; own marbles only | `legal_actions`, `apply_action` | Probe: actions contain only current player's group and transition ends turn. | None |
| Move to the next hole only; six directions | `DIRECTIONS`, `_result` | Probe: every destination differs by one listed axial direction. | None |
| Move one, two, or three marbles; same direction | `legal_actions`, `_line`, `_result` | Probe: group sizes are 1..3 and one direction translates the group. | None |
| Destination hole must be free | `_result` | Probe: broadside/ordinary inline moves reject occupied destination. | None |
| No more than three marbles of one color | `legal_actions` | Probe: no generated group exceeds three. | None |
| A longer row may be split by moving 1..3 | `legal_actions` | Probe: eligible contiguous subsets are generated independently. | None |
| Abbildung 2: movement in a straight line | `_result` inline branch | Probe: rear vacates and front enters next hole. | None |
| Abbildung 3: movement to the side | `_result` broadside branch | Probe: all translated destinations must be on-board and empty. | None |
| Completed movement cannot be changed | immutable `GameState`; atomic `apply_action` | Probe: transition returns a new state; no undo action exists. | None |
| Sumito; Abbildung 4: 2-to-1, 3-to-1, 3-to-2 | `_result` push branch | Probe fixtures for each numerical superiority push. | A-02 |
| Sumito only in a straight line | `_result` (`inline`) | Probe: broadside movement never pushes. | None |
| Abbildung 5: blocked/non-Sumito cases | `_result` | Probe: reject no free cell behind defender, intervening empty cell, and non-collinear group. | A-02 |
| Sumito attack is optional | `legal_actions` | Source-only probe: ordinary alternative moves remain legal; there is no forced-attack phase. | None |
| Patt: 1-to-1, 2-to-2, 3-to-3 | `_result` (`len(chain) >= len(group)`) | Probe all equal-count pushes are rejected. | None |
| More than three in a Patt: excess ignored | `_result`, maximum generated group size 3 | Probe: four-versus-three cannot be selected as four, so remains 3-to-3. | None |
| Resolve Patt by attacking on another line/angle; Abbildung 7 | `legal_actions` | Geometric consequence of independently generated straight groups; diagram labels are illustrative, not extra actions. | None |
| Hinausschieben / Abbildung 8 | `_result`, `captures` | Probe: legal superior push with no cell beyond increments mover's captures. | None |
| Wer gewinnt? first to push out six | `apply_action`, `returns` | Probe: capture count 6 terminates with +1/-1 returns. | None |
| Gegen die Zeit | Not implemented | Optional real-time recommendation (“can”); contract forbids runtime input and rulebook supplies no mandatory clock choice or timeout result. | None |

The profile's canonical `pass` vocabulary is serializable by
`action_to_data`/`action_from_data`, but `pass` is never legal because the
rulebook requires a movement on a turn and supplies no pass rule.
