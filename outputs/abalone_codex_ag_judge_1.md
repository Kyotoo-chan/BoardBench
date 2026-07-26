## Review result

**Score: 0.80 — confidence: high.** The implementation accurately covers the printed setup, six-direction movement, inline/broadside movement, Sumito, Patt, ejection, turn alternation, immediate sixth-ejection victory, returns, and public observation. Two material approved software-contract requirements are contradicted: forced passes and unique action serialization.

No optional-clock, draw, repetition, or outside-rule assumptions were introduced.

## Findings

### Major — Forced pass is never legal

- Canonical fact ID: `ABAL-G-PASS`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.”
- Conflicting symbols/transitions: `Game.legal_actions`, `Game.apply_action`
- Expected: When the active player has no legal movement, `legal_actions` returns exactly one pass. A pass is unavailable whenever any movement exists, and applying the forced pass advances the turn.
- Implemented: `legal_actions` returns an empty list when no generated movement succeeds. It never generates `Action("pass", ...)`. Because `apply_action` requires membership in `legal_actions`, every pass is rejected, even though pass objects can be parsed and serialized.
- Impact: A valid no-movement state deadlocks instead of continuing. This materially contradicts the approved turn-flow decision.

### Major — Multiple accepted serializations can describe the same movement

- Canonical fact ID: `ABAL-G-ACTION-UNIQUE`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved human decisions,” item 5
- Exact evidence: “Exactly one canonical serialized action represents each physical movement.”
- Conflicting symbols: `Game.action_to_data`, `Game.action_from_data`, `Game.action_to_name`, `Game.name_to_action`
- Expected: A multi-marble group has one canonical ordering in serialized actions; permutations must either be normalized to that ordering or rejected.
- Implemented: Data and name parsing accept the group in any supplied order, while serialization preserves that order. A two- or three-marble movement therefore has multiple accepted encodings. Moreover, `legal_actions` generates only sorted tuples, so a permuted encoding can parse successfully but then be rejected by `apply_action`.
- Impact: The public action contract is non-canonical and permits accepted-but-unexecutable aliases.

## Rule-area coverage

| Rule area | Status | Relevant facts |
|---|---|---|
| Players and initial setup | Conforms | `ABAL-C-PLAYERS`, `ABAL-C-SETUP-FIGURE`, `ABAL-C-BOARD-61`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` |
| Player/color mapping and first turn | Conforms | `ABAL-C-TURN-ORDER`, `ABAL-G-PLAYER-MAPPING` |
| One-step, six-direction movement | Conforms | `ABAL-C-ONE-MOVE`, `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` |
| Group formation and maximum size | Conforms | `ABAL-C-GROUP-SIZE`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-MAX-THREE`, `ABAL-C-SUBSET-LONG-ROW` |
| Inline and broadside movement | Conforms | `ABAL-C-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION`, `ABAL-G-BROADSIDE-DESTINATIONS` |
| Sumito legality | Conforms | `ABAL-C-SUMITO-SUPERIOR` through `ABAL-C-SUMITO-OPTIONAL` |
| Patt and crossing attacks | Conforms | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-FOUR-THREE`, `ABAL-C-PATT-WITHDRAW`, `ABAL-C-PATT-CROSSING` |
| Ejection and victory | Conforms | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SIXTH-WINS`, `ABAL-G-TERMINAL-API` |
| Forced pass | Fails | `ABAL-G-PASS` |
| Returns | Conforms | `ABAL-G-RETURNS` |
| Public observation | Conforms | `ABAL-G-PUBLIC-STATE` |
| Canonical action encoding | Fails | `ABAL-G-ACTION-UNIQUE` |
| Chance/private information | No material issue; deterministic mapping is approved | `ABAL-C-COLOR-LOTTERY`, `ABAL-G-PLAYER-MAPPING` |
| Clock, draw, repetition | Excluded or unresolved; not penalized | `ABAL-C-CLOCK-OPTIONAL`, `ABAL-G-CLOCK`, `ABAL-G-DRAW` |

## Missing deterministic scenarios

Recommended scenarios not evidenced by the permitted review packet:

1. A nonterminal state with no movement produces exactly one pass; applying it changes only turn-related state.
2. Pass is absent whenever at least one movement exists.
3. Every two- and three-marble action rejects or normalizes every noncanonical group permutation across both name and data APIs.
4. Every generated legal action survives name/data round trips and remains applicable.
5. A sixth edge ejection simultaneously sets terminal, winner, phase, empty legal actions, winner-retained `current_player`, and `[+1,-1]` returns.
6. Broadside moves with one off-board or occupied destination are rejected.
7. `4v3` remains blocked while legal withdrawal, broadside escape, and crossing-angle Sumito remain available.
8. Moving a one-to-three-marble subset out of a longer row remains legal where its destinations permit it.

## Material questions for a human

The approved facts decide the scored behavior above. One unscored API question remains: should `state_from_data` reject relationally inconsistent snapshots—for example, terminal/winner/phase combinations that disagree or capture totals incompatible with the board—or is it intentionally only a structural decoder? The rulebook does not define deserialization validation.

The source still supplies no draw, repetition, move-limit, or clock-expiration result. The implementation makes no conflicting outcome assumption, so these omissions are not findings.

score: 0.80
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true