score: 0.28  
confidence: high

The inventory, setup, payout tables, hand ordering, basic phase sequence, recycling, and tie-break are substantially represented. However, terminal scoring is fundamentally wrong, illegal transitions are accepted directly, and multi-player phase-three planting is incomplete.

## Findings

### Critical

1. Hand cards are incorrectly converted into coins at game end.

- Canonical fact ID: `BASE-SCORE-01`
- Evidence type: `rule_quote`
- Source ID: `BOHN-BASE-RULES`
- Locator: PDF page 2, “Ende des Spiels”
- Exact evidence: “Die Karten auf der Hand zählen nicht mehr.”
- Conflicting code: `_finish`, especially `p["coins"] += len(p["hand"])` at implementation line 193.
- Expected: Harvest all fields; ignore every hand card; determine scores solely from coin-pile cards.
- Implemented: Every remaining hand card becomes one coin. This can change scores, ties, and the winner.

2. `apply_action` does not enforce phase, actor, or legality constraints.

- Canonical fact ID: `BASE-PLANT-02`
- Evidence type: `rule_quote`
- Source ID: `BOHN-BASE-RULES`
- Locator: PDF page 1, “1. Phase”
- Exact evidence: “Du musst die vorderste Bohnenkarte … anbauen.”
- Conflicting code: `Game.apply_action` lines 206–281; notably the unconditional `pass` handling at lines 215–222.
- Expected: With a nonempty hand in `plant_first`, passing must be rejected; actions from the wrong phase, wrong actor, invalid field, or prohibited harvest must likewise be rejected.
- Implemented: Any syntactically constructed `Action` is dispatched without checking membership in `legal_actions`. A player can pass the mandatory first planting, draw or reveal out of phase, spoof another player’s harvest, violate singleton protection, or cause index errors. Legal play therefore depends entirely on a trusted caller.

### Major

3. Only the active player can plant phase-three cards; trading partners’ received cards remain stranded.

- Canonical fact ID: `BASE-PHASE3-01`
- Evidence type: `rule_quote`
- Source ID: `BOHN-BASE-RULES`
- Locator: PDF page 2, “3. Phase”
- Exact evidence: “Alle, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen.”
- Conflicting code: `legal_actions` lines 161–168 and `apply_action` lines 224–236 use only `pending_received[active_player]`; `end_trade` merely enters `plant_received`.
- Expected: Every affected player plants all cards they received, in an order chosen by that player. The active player additionally plants untraded revealed cards.
- Implemented: Only the active player receives planting actions. Cards staged for partners are never processed and can remain outside all hands and fields through later turns or termination.

4. The environment cannot represent a pure gift from a non-active player to the active player.

- Canonical fact ID: `BASE-TRADE-07`
- Evidence type: `rule_quote`
- Source ID: `BOHN-BASE-RULES`
- Locator: PDF page 2, gift rule
- Exact evidence: “Auch als besondere Form des Handelns dürft ihr euch auch Bohnenkarten schenken.”
- Conflicting code: trade generation lines 143–159; `omask` begins at 1, so the active player must always offer at least one card. Only active-to-partner gifts are generated.
- Expected: A gift is a zero-for-cards trade requiring the recipient’s consent, including a partner offering cards to the active player.
- Implemented: Requested cards are allowed only when the active player also offers something, so partner-to-active gifts are absent.

5. Harvest actions are missing at exposed stable decision boundaries.

- Canonical fact ID: `D-BASE-INTERRUPT`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Locator: JSON Pointer `/approved_evaluator_decisions/2`
- Exact evidence: “Represent ‘jederzeit’ harvesting at every stable player decision boundary, including off-turn.”
- Conflicting code: `legal_actions` returns only accept/reject in `trade_response` and only `draw` in `draw`.
- Expected: Before resolving these exposed decisions, eligible players can harvest, without interrupting the subsequent atomic response or draw operation.
- Implemented: Harvesting is unavailable at both boundaries.
- Provenance note: This is a contradiction of the approved evaluator decision, not an independently explicit definition of atomic interface timing in the printed rulebook.

No minor findings.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Components and player count | Correct |
| Field count and initial hands | Correct |
| Start player/card | Represented internally as fixed player 0 |
| Immutable hand order | Correct in ordinary legal flow |
| First/second planting | Legal-action list mostly correct; application enforcement critically deficient |
| Reveal and recycling | Correct for ordinary flow |
| Trading and consent | Partial; received-card re-trading is prevented, but one gift direction is absent |
| Phase-three planting | Major multi-player transition missing |
| Phase-four draw | Correct in ordinary flow |
| Harvest legality and payouts | Tables and generated actions correct; direct application can bypass restrictions |
| Third depletion | Core continuation/immediate-ending logic represented |
| Final harvest and scoring | Final harvest present; hand scoring critically wrong |
| Winner and tie-break | Tie-break correct, but winner is corrupted by hand scoring |
| Observations/private information | Generally follows the approved interface decision; debug `render` is fully revealing |
| Serialization/state integrity | Structural checks exist, but semantic state invariants are weak |

## Deterministic scenarios needed

- End with unequal hand sizes but equal legitimate coin totals; hands must not affect the winner.
- Attempt `pass` during `plant_first` with a nonempty hand; require rejection.
- Submit draw, reveal, plant, harvest, and trade actions from wrong phases or actors; require rejection without mutation or crash.
- Accept a trade that gives cards to both players; require each player to plant all received cards in their chosen order.
- Complete phase three after third depletion with a trading partner holding received cards; plant all such cards before final scoring.
- Offer a partner-to-active pure gift; test both acceptance and rejection.
- Test legal off-turn harvesting at `trade_response` and immediately before the atomic phase-four draw.
- Attempt to harvest a protected singleton through direct `apply_action`; require rejection.

## Material questions for a human

- The packet determines the winner but does not define the API utility convention. Should `returns()` remain a one-hot winner vector, return final coin totals, or use another payoff representation? No penalty was assigned for its current one-hot convention.
- Should deserialized states be required to enforce complete card conservation, homogeneous fields, valid player IDs, field counts, and phase-specific invariants? The publisher rules establish these invariants, but the required trust boundary for `state_from_data` is not specified.

```text
score: 0.28
confidence: high
critical_issues: 2
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```