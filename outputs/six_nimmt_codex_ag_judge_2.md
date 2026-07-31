## 1. Score

**Score: 0.88 — confidence: high.**

The normal game path correctly implements setup, hidden commitments, joint reveal, ascending/dynamic resolution, both capture mechanisms, scoring, repeated games, the strict-over-66 threshold, shared minimum-score winners, and terminal returns. The main material weakness is that public state deserialization admits an excluded match-target variant. Two smaller state/rendering issues do not affect ordinary internally generated play.

## 2. Findings

### Major — Deserialization admits non-default match targets in base-game states

- Canonical fact: `6N-C-ALTERNATE-TARGET`
- Evidence type: `rule_quote`
- Source: `6NIMMT-V23-RULES`, PDF page 2
- Exact evidence: “kann ... eine andere Punktzahl oder Anzahl an Spielen vereinbart werden”
- Approved expectation: “Players may agree on another target or game count, but this condition uses the printed default.”
- Conflicting code:
  - `Game.initial_state()` correctly sets `"match_target": 66`.
  - `Game.state_from_data()` only requires `type(cfg["match_target"]) is int`.
  - `_finish_round()` then uses the imported value in `total_bullheads > match_target`.
- Expected: Every accepted state labeled `variant == "base"` in this source condition must retain target 66.
- Implemented: A serialized base state with any integer target—including 0, 50, or a negative value—is accepted and changes when the match terminates.
- Impact: The public state-loading transition can silently enable a variant explicitly excluded by the declared condition, materially changing match length and potentially the winner.

### Minor — Terminal rendering double-displays the completed game’s points

Canonical facts: `6N-C-GAME-SCORE`, `6N-C-WINNER-MINIMUM`.

At game end, `_finish_round()` adds `game_bullheads` to `total_bullheads` but leaves `game_bullheads` unchanged. `render()` subsequently formats each score as `total_bullheads + game_bullheads`. Thus, after a terminal game, a player whose cumulative total is already 70 and whose final game contributed 15 is displayed as `70+15`, visually suggesting 85. Winner calculation remains correct, so this is localized to presentation/state semantics.

### Minor — Accepted serialized states are not checked against core structural invariants

`state_from_data()` checks container shapes but does not enforce, among other things:

- exactly four nonempty rows;
- exactly `configuration.players` player records;
- consecutive, unique player IDs;
- cards restricted to 1–104 with one-copy inventory;
- row length at most five and ascending order;
- score consistency with captured cards;
- phase/current-player/pending/terminal consistency;
- consistency between the serialized player count and the receiving `Game`.

Consequently, it can accept payloads that later crash—for example, an empty row reaches `row[-1]` in `_continue_resolution()`—or deadlock through inconsistent phase fields. This does not arise from normal internally generated play, so it is minor rather than a core-flow failure.

### Questions

No rule contradiction was found regarding seat-ordered digital commitments, shared winners, deterministic shuffling/reset, pending low-card choices, observation privacy, or ±1 terminal returns. Those are adjudication-dependent digital choices recorded as approved in the supplied fact inventory.

## 3. Rule-area coverage

| Rule area | Result | Relevant claims |
|---|---|---|
| Player range and base scope | Mostly correct; imported target not fixed at 66 | `6N-C-PLAYER-RANGE`, `6N-C-ALTERNATE-TARGET` |
| Deck and setup | Correct in generated states | `6N-C-CARD-TOTAL`, `6N-M-CARD-IDENTITIES`, `6N-C-SHUFFLE`, `6N-C-DEAL-TEN`, `6N-C-FOUR-ROWS`, `6N-C-RESERVE-COUNT` |
| Private commitments | Correct seat-ordered hidden protocol and joint reveal | `6N-C-FACE-DOWN-COMMIT`, `6N-C-JOINT-REVEAL`, `6N-M-COMMIT-PROTOCOL` |
| Placement order | Correct ascending and dynamically updated resolution | `6N-C-ASCENDING-RESOLUTION`, `6N-C-DYNAMIC-RESOLUTION` |
| Ordinary placement | Correct closest lower row | `6N-C-ROW-ASCENDING`, `6N-C-MIN-DIFFERENCE` |
| Sixth-card capture | Correct five-card capture and played-card starter | `6N-C-ROW-MAX-FIVE`, `6N-C-FULL-CAPTURE`, `6N-C-SIXTH-STARTER` |
| Low-card capture | Correct pending choice among all four rows | `6N-C-LOW-CHOOSE-ROW`, `6N-C-LOW-STARTER`, `6N-C-TIP-NONBINDING` |
| Captured cards | Correctly separated from hands and scored | `6N-C-CAPTURE-FACE-DOWN`, `6N-C-CAPTURE-NOT-HAND`, `6N-C-BULLS-ARE-POINTS` |
| Bullhead inventory | Correct precedence and values | `6N-M-BULL-INVENTORY`, `6N-C-FIVE-SCORE`, `6N-C-TEN-SCORE`, `6N-C-DOUBLE-SCORE`, `6N-C-55-SCORE` |
| Game progression | Correct ten rounds and fresh-game setup | `6N-C-TEN-ROUNDS`, `6N-C-GAME-END`, `6N-C-GAME-SCORE`, `6N-C-NEW-GAME` |
| Match termination/winner | Correct in generated states; target mutable on import | `6N-C-MATCH-THRESHOLD`, `6N-C-WINNER-MINIMUM`, `6N-M-TIE-WINNER` |
| Information model | Opponent hands, commitments, and captured identities remain hidden | `6N-M-OBSERVATION` |
| Returns | Approved shared-winner +1 / other-player −1 behavior implemented | `6N-M-RETURNS` |
| Serialization | Round-trip shape exists, but canonical invariants are under-validated | Multiple setup/transition claims |

## 4. Missing deterministic scenarios

Because no scenario files were inspected, these are recommended coverage cases rather than claims about an existing test suite:

1. Reject an imported base state whose `match_target` is not 66.
2. Exactly 66 after a completed game continues; 67 terminates.
3. A terminal render does not visually count the last game twice.
4. Reject imported states with zero, three, or five rows, or any empty row.
5. Reject duplicate, missing, or out-of-range card identities.
6. Reject player-list length or player-ID mismatches.
7. Verify a low-card choice may select any row, including a non-minimum-point row.
8. Verify later revealed cards use the row created by an earlier low-card choice.
9. Verify a sixth-card capture takes exactly the prior five cards, never the played sixth card.
10. Verify ten-player setup has 100 hand cards, four row starters, and an empty reserve.
11. Verify repeated calls to the seeded reset/initial-state path reproduce the same initial deal.
12. Verify opponent observations never reveal committed cards before joint reveal or captured identities afterward.
13. Verify tied minimum totals produce multiple winners and +1 for each.
14. Reject phase/current-player/pending combinations that would deadlock.

## 5. Material questions for a human

- Should `state_from_data()` be a strict trust-boundary validator for canonical, reachable game states? The rulebook does not define serialization validation, but the current permissiveness permits crashes and excluded configurations.
- At terminal state, should `game_bullheads` be cleared, or should rendering explicitly state that it is already included in `total_bullheads`?

```text
score: 0.88
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 2
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```