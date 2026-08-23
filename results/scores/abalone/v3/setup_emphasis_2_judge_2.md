score: 0.87 — confidence: high. The printed base-game mechanics are implemented accurately, including setup, movement, Sumito, ejection, and victory. Two approved software-contract decisions are contradicted: forced passing and unique action serialization.

## Findings

### Major — No forced pass, causing a nonterminal dead end

- Canonical fact ID: `ABAL-G-PASS`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.”
- Conflicting symbols/transitions: `Game.legal_actions`, `Game._result`, `Game.apply_action`
- Expected: If the active player has no legal movement, exactly one pass action is legal; applying it continues turn flow. Pass must be unavailable otherwise.
- Implemented: `legal_actions` returns an empty list when no movement exists. `_result` rejects every action whose type is not `"move"`, so the serialized `"pass"` action can never be applied.
- Impact: A valid nonterminal no-move position becomes stuck with no available transition.

### Major — Multiple serialized actions can represent one physical movement

- Canonical fact ID: `ABAL-G-ACTION-UNIQUE`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved human decisions,” item 5
- Exact evidence: “Exactly one canonical serialized action represents each physical movement.”
- Conflicting symbols: `Game.name_to_action`, `Game.action_from_data`, `Game._result`, `Game.action_to_name`, `Game.action_to_data`
- Expected: Multi-marble groups have one canonical coordinate ordering; alternative permutations must be normalized or rejected.
- Implemented: Deserializers preserve arbitrary group order, while `_line_direction` and `_result` treat the group geometrically as a set. Consequently, reversed and other permuted coordinate lists can encode and execute the same movement. `name_to_action` considers each permutation canonical because it only checks reproduction of that same ordering.
- Impact: The generated `legal_actions` list is deduplicated, but the public action parsers still admit aliases, violating the approved canonical action contract.

### Question — Semantic consistency of deserialized states is unspecified

`Game.state_from_data` accepts combinations such as six captures with `terminal=False`, a winner on a live state, or terminal phase/flag disagreement. Such states can behave contrary to immediate sixth-ejection victory (`ABAL-C-SIXTH-WINS`), but the packet does not explicitly require deserialization to reject semantically inconsistent or unreachable payloads. This is therefore not scored as a contradiction.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Players and setup | Pass | Two players; 61 pits; exact 14/14 Figure-1 rows (`ABAL-C-PLAYERS`, `ABAL-C-SETUP-*`, `ABAL-C-BOARD-61`). |
| Initial turn and alternation | Pass | Player 0 is black and starts; successful nonterminal moves alternate (`ABAL-C-TURN-ORDER`). |
| No-move turn | Fail | Forced pass is absent (`ABAL-G-PASS`). |
| Ordinary movement | Pass | One to three contiguous, straight own marbles; one step; six directions; empty destinations. |
| Broadside movement | Pass | Every corresponding destination must be on-board and empty (`ABAL-G-BROADSIDE-DESTINATIONS`). |
| Sumito and Patt | Pass | Strict superiority, legal patterns, adjacency, blocking, gaps, collinearity, and maximum effective strength are handled. |
| Ejection | Pass | Edge exception and removal of the final defender are correct (`ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`). |
| Terminal transition | Pass | Sixth capture immediately terminates; winner remains current player; legal actions become empty. |
| Returns | Pass | `[0,0]` before terminal and winner/loser `[+1,-1]` by player ID. |
| Public observation | Pass | Required board, turn, captures, terminal, winner, phase, and move-number fields are public. |
| Action serialization | Fail | Parsers admit coordinate-order aliases (`ABAL-G-ACTION-UNIQUE`). |
| Chance/private information | Pass | No private information or gameplay randomness is introduced; seed metadata does not affect play. |
| Draws and clocks | Unscored | Draw/repetition rules are absent; optional clock play is outside declared scope. |

## Missing deterministic scenarios

Because reviewing scenario files was prohibited, these are scenarios that should be ensured, not assertions about the existing suite:

1. A nonterminal state with no legal movement exposes exactly one pass; applying it advances the turn.
2. Pass is rejected whenever at least one movement exists.
3. Reversed and otherwise permuted two- and three-marble groups cannot produce additional serialized aliases.
4. Canonical action round-trips preserve exactly one representation.
5. Sixth edge ejection simultaneously verifies terminal state, winner/current-player identity, empty legal actions, and `+1/-1` returns.
6. If semantic state validation is required, reject inconsistent capture, terminal, winner, and phase combinations.

## Material questions for a human

- Should `state_from_data` reject internally inconsistent but structurally valid payloads, or is it permitted to load arbitrary analysis positions?
- No rulebook clarification is needed for the two scored findings; both are resolved by approved human decisions.
- Draw, repetition, and move-limit outcomes remain unspecified, but they are explicitly unscored under the supplied scope.

score: 0.87
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true