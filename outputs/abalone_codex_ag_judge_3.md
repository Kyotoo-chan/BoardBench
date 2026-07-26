Score: 0.95 — confidence: high. The movement, Sumito, setup, ejection, victory, serialization, observation, and return rules align closely with the approved facts. One material forced-pass transition is absent and can leave a nonterminal state without an applicable action.

## Findings

### Major — Forced pass is never legal

- Canonical fact ID: `ABAL-G-PASS`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.”
- Conflicting symbols/transitions:
  - `Game.legal_actions`
  - `Game.apply_action`
  - `Action(type="pass", ...)`
- Expected: If the active player has no legal movement, the legal-action list contains exactly one pass. Pass must remain unavailable whenever any movement exists.
- Implemented: `legal_actions()` returns an empty list when no movement exists. Although pass actions can be parsed and serialized, they are never returned as legal, so `apply_action()` rejects every pass.
- Impact: A no-movement, nonterminal position cannot advance. This is a material turn-flow omission, though such positions appear uncommon enough not to rate as a common critical deadlock.

No critical or minor contradictions were found.

## Rule-area coverage

| Rule area | Status | Canonical claims |
|---|---|---|
| Players and initial setup | Conforms | `ABAL-C-PLAYERS`, `ABAL-C-SETUP-FIGURE`, `ABAL-C-BOARD-61`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` |
| Player/color mapping and first turn | Conforms to approved decision | `ABAL-C-TURN-ORDER`, `ABAL-G-PLAYER-MAPPING` |
| One-step group movement | Conforms | `ABAL-C-ONE-MOVE`, `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS`, `ABAL-C-GROUP-SIZE`, `ABAL-C-SAME-DIRECTION`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-MAX-THREE`, `ABAL-C-SUBSET-LONG-ROW` |
| Inline and broadside movement | Conforms | `ABAL-C-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION`, `ABAL-G-BROADSIDE-DESTINATIONS` |
| Sumito legality | Conforms | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS`, `ABAL-C-SUMITO-INLINE`, `ABAL-C-SUMITO-ADJACENT`, `ABAL-C-SUMITO-FREE-BEHIND`, `ABAL-C-SUMITO-BLOCKED`, `ABAL-C-SUMITO-GAP`, `ABAL-C-SUMITO-COLLINEAR`, `ABAL-C-SUMITO-OPTIONAL` |
| Patt and alternative movement | Conforms | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-FOUR-THREE`, `ABAL-C-PATT-WITHDRAW`, `ABAL-C-PATT-CROSSING` |
| Ejection and victory | Conforms | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SIXTH-WINS` |
| Terminal state and returns | Conforms to approved decisions | `ABAL-G-TERMINAL-API`, `ABAL-G-RETURNS` |
| Forced/voluntary pass | Major omission | `ABAL-G-PASS` |
| Public observation | Conforms to approved decision | `ABAL-G-PUBLIC-STATE` |
| Canonical action identity | Conforms for legal actions | `ABAL-G-ACTION-UNIQUE` |
| Chance/private information | No unsupported gameplay chance or private state found | `ABAL-C-COLOR-LOTTERY`, `ABAL-G-PLAYER-MAPPING` |
| Optional clock, draw, repetition | Correctly omitted from base scope | `ABAL-C-CLOCK-OPTIONAL`, `ABAL-G-CLOCK`, `ABAL-G-DRAW` |

## Missing deterministic scenarios

Recommended deterministic coverage:

1. A nonterminal state with no legal movement: exactly one pass must be legal and applicable.
2. A state with at least one movement: pass must not appear and must be rejected.
3. Broadside movement where one destination is occupied or off-board: reject the entire action without partial movement.
4. Fifth-to-sixth ejection: immediate terminal state, no legal actions, winner remains current player, and returns are `+1/-1`.
5. Equivalent reordered or noncanonical group encodings: ensure only the canonical serialized action is accepted as legal.
6. Four attackers facing three defenders: verify selecting any permissible subset cannot create an illegal 4v3 strength advantage.

## Material questions for a human

None. The publisher rulebook omits forced-pass behavior, but the approved human decision resolves it. Draw, repetition, clock-expiration, and box-inventory questions remain explicitly outside the scored base-game scope.

```text
score: 0.95
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```