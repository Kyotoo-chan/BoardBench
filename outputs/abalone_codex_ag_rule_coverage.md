# Rule coverage

Only the four supplied German rulebook pages were used as rule evidence. Contract/profile items are representation only.

| Source section / named item | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Ziel des Spieles | `Game.apply_action`, `Game.is_terminal`, `Game.returns` | Self-check rollouts exercise terminal predicates; direct six-capture fixture covered by canonical reconstruction | A-03 |
| Vorbereitung; Abbildung 1 | `Game.initial_state` | Initial board count and placement inspected via render/canonical state | A-01 |
| Der Spielablauf: alternating turns; black starts | `Game.initial_state`, `Game.apply_action` | Rollout checks player alternation | none |
| One movement only; own marbles | `Game.legal_actions`, `Game._result` | Every generated action is applied by self-check | none |
| Adjacent hole; six directions | `DIRS`, `Game._result` | Generated targets are one axial neighbor | none |
| Move one, two, or three; same direction; no more than three of a color | `Game._result`, `Game.legal_actions` | Generated group sizes limited to 1..3 | A-02 |
| Split a longer row by moving 1..3 | `Game.legal_actions` | All consecutive subgroups are generated independently | A-02 |
| Two movement types; Abbildungen 2 and 3 (inline / sideways) | `Game._result` | Inline and broadside actions occur in rollout; broadside requires vacant destinations | none |
| Executed movement cannot be changed | `Game.apply_action` | Atomic transition; no undo/pending phase exists | none |
| Sumito; 2-to-1, 3-to-1, 3-to-2 (Abbildung 4) | `Game._result` | Strength comparison and consecutive enemy scan encode all three named combinations | A-02 |
| Sumito only straight, adjacent opposing colors, free hole behind attacked marbles | `Game._result` | Illegal equal/blocked pushes rejected by action generation | A-02 |
| Abbildung 5: no Sumito due no free hole / empty gap / not straight | `Game._result`, `_line_direction` | Each stated blocker has a direct predicate | none |
| Attack optional even when possible | `Game.legal_actions` | Generator retains every legal non-attack move alongside pushes | none |
| Patt; 1-to-1, 2-to-2, 3-to-3 (Abbildung 6) | `Game._result` | `len(opponents) >= len(group)` rejects all three | none |
| More than three in a Patt: only nearest three count | `Game._result` | Friendly action groups never exceed three, so equal-or-larger opposition blocks | none |
| Resolve Patt by attacking from another line/angle; Abbildung 7 | `Game.legal_actions` | No persistent Patt state; all directions/groups are regenerated each turn | none |
| Hinausschieben; Abbildung 8 | `Game._result`, `Game.apply_action` | Off-board final enemy increments mover's capture count | none |
| Wer gewinnt? first to push out six | `Game.apply_action`, `Game.returns` | Terminal transition occurs at capture count six | A-03 |
| Gegen die Zeit (optional examples; official competitions) | not implemented | Source presents clocks as optional and supplies no clock-selection protocol or timeout result | A-03 |

## Representation-only coverage

`state_to_data`, `state_from_data`, `action_to_data`, `action_from_data`, and `observation_to_data` implement the exact schemas and required fields from `GAME_PROFILE.json`. The profile's `pass` type is serializable but is never legal because the rulebook supplies no pass rule. There is no chance or private information in the supplied rules; the seed is retained canonically and no chance operation occurs.
