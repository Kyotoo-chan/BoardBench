score: 0.86  
confidence: high

The implementation closely matches the printed setup, movement, Sumito, ejection, and victory rules. The material defect is the missing forced-pass transition required by the approved human decision.

## Findings

### Major — No forced pass when the active player has no legal movement

- Canonical fact ID: `TURN-01`, supplemented by the approved forced-pass human decision.
- Evidence type: `human_decision`.
- Rulebook quote: “Die Spieler sind abwechselnd an der Reihe. Schwarz fängt immer an.” — page 1, “Der Spielablauf”.
- Approved decision: “if and only if a player has no legal movement, expose one forced pass that advances the turn.” — `canonical_rulefacts.md`, “Proposed BoardBench interface conventions”.
- Conflicting symbols/transitions: `Game.legal_actions`, `Game.apply_action`, and `Game.current_player`.
- Expected: If at least one movement exists, no pass is available. If no movement exists, exactly one forced-pass action advances play to the opponent.
- Implemented: `legal_actions()` returns an empty tuple, while `current_player()` still identifies the active player and `apply_action()` accepts only listed `"move"` actions. Such a state has no outgoing transition and deadlocks.
- Scope: The implemented behavior correctly excludes voluntary passes when moves exist; only the adjudicated no-movement branch is missing.

No critical or minor contradictions were identified.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Two-player setup | Pass | 61-cell radius-four board; 14 black and 14 white marbles in the Figure 1 arrangement |
| First player/alternation | Pass except no-move case | Black starts; successful moves alternate turns |
| One atomic movement | Pass | Every action represents one movement |
| Group selection | Pass | Contiguous straight groups of 1–3 own marbles |
| Six directions/one-pit movement | Pass | Six axial directions; every selected marble advances one adjacent pit |
| Inline movement | Pass | Parallel movement into empty space is supported |
| Broadside movement | Pass | All corresponding destinations must be on-board and empty |
| Sumito strengths | Pass | Supports 2v1, 3v1, and 3v2; rejects equal or stronger defenders |
| Sumito geometry/blocking | Pass | Requires inline adjacency and an empty on-board destination or board edge |
| Patt | Pass | Selection is capped at three, preventing 4v3 from gaining extra force |
| Ejection | Pass | Edge-pushed defender is removed and counted by color |
| Sixth-ejection victory | Pass | Terminal immediately after six opposing marbles are ejected; returns identify the winner correctly |
| Draw/repetition | Pass/out of scope | No unsupported draw terminal was added |
| Clock | Pass/out of scope | Optional clock mechanics are excluded |
| Forced pass | **Fail** | Required no-legal-movement transition is absent |
| Action serialization | Pass | Canonical names round-trip through the provided conversion methods |

## Missing deterministic scenarios

The module’s embedded assertions cover only initial inventory, existence of an opening action, and action-name round trips. Deterministic coverage should include:

- Exact 61-pit Figure 1 coordinate mapping and all 28 starting occupants.
- Black as the initial player and strict alternation after a nonterminal move.
- Single-marble, two-marble, and three-marble inline moves.
- Legal broadside moves for two and three marbles.
- Rejection of disconnected, bent, opponent-owned, and four-marble selections.
- Legal 2v1, 3v1, and 3v2 Sumito.
- Rejection of 1v1, 2v2, 3v3, 4v3-equivalent, gapped, blocked, and non-collinear pushes.
- Edge ejection without an on-board empty destination.
- Fifth ejection remaining nonterminal and sixth ejection ending immediately with correct returns.
- No pass while any movement exists.
- Exactly one forced pass when no legal movement exists, followed by the opponent’s turn.
- Action-name rejection for malformed or noncanonical encodings.

## Material questions for a human

None requiring additional rulebook adjudication. The printed rules do not specify the no-legal-movement case, but the approved human decision already resolves it. A deterministic fixture should establish that the implementation honors that decision even if such a position is rare or only adapter-constructed.

score: 0.86
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true