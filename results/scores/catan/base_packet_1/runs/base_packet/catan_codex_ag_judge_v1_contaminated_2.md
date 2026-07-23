score: 0.64  
confidence: high

The module covers most core mechanics coherently, including the fixed setup, production, robber flow, building legality, awards, and development-card effects. The score is reduced by four major issues: one printed privacy contradiction and three deviations from approved terminal/reveal decisions.

## Findings

### Major — Printed-rule contradiction

1. Domestic-trade legal actions disclose opponents’ private resource holdings.

- Canonical fact: `CAT-INFO-01`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF p. 2
- Exact evidence: “Seine Rohstoffkarten hält jeder Spieler verdeckt in der Hand.”
- Conflicting symbol: `Game.legal_actions`, `trade_offer` branch, especially lines 220–229.
- Expected: An opponent’s resource identities and quantities remain private while an offer is constructed.
- Implemented: A `take` action is offered only while `take[r] < opponent.resources[r]`. The active player can therefore test every resource repeatedly and infer each opponent’s exact inventory from when actions disappear.
- Impact: Material private-information leakage during a common action phase.

### Major — Approved human-decision deviations

2. Victory is not checked when a player becomes active.

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, `CAT-D-WIN`
- Exact evidence: “Check victory after every completed atomic action or committed subaction; if the active player then has at least ten, terminate immediately. This includes turn start before rolling…”
- Conflicting transition: `Game.apply_action`, `end_turn` branch, lines 328–331.
- Expected: After the next player becomes active, victory is checked before that player must roll.
- Implemented: The transition sets the new active player and phase to `roll` without calling `_victory`. The player can roll, trade, build, or even end the turn without winning unless another score-affecting action happens to invoke `_victory`.
- Impact: A rightful winner can be delayed indefinitely or miss the winning turn entirely.

3. Winning with the first free Road Building road crashes instead of returning a terminal state.

- Canonical facts: `CAT-D-WIN`, `CAT-D-ROAD-CARD`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, `CAT-D-WIN` and `CAT-D-ROAD-CARD`
- Exact evidence:
  - `CAT-D-WIN`: “This includes … the first free road of Road Building.”
  - `CAT-D-ROAD-CARD`: “Re-evaluate legality and victory after each road.”
- Conflicting transition: `Game.apply_action` → `place_free_road` and `Game._place_road`, lines 316–318 and 413–415.
- Expected: If the first free road grants enough points, the game terminates immediately and the action returns that terminal state.
- Implemented: `_place_road` invokes `_victory`, which sets `pending=None`; control then returns to line 317 and evaluates `d["pending"]["remaining"] -= 1`, causing an exception.
- Impact: A valid, explicitly adjudicated winning transition cannot complete.

4. Hidden victory-point cards are never revealed when they establish victory.

- Canonical fact: `CAT-D-VP-REVEAL`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, `CAT-D-VP-REVEAL`
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten…”
- Conflicting symbols: `Game._score` and `Game._victory`, lines 155–163 and 441–443.
- Expected: Victory detection removes/reclassifies the minimum necessary hidden VP cards into publicly revealed state, in hand order.
- Implemented: `_score` silently counts all hidden VP cards and `_victory` only sets terminal fields. The cards remain in the private development hand, while `public_scores` can remain below the winning threshold.
- Impact: The winner is declared without the required public proof, and the approved minimum-reveal procedure is absent.

No critical or minor findings were established from the assigned evidence.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Fixed setup and inventory | Pass | Four players, terrain/numbers, robber, pieces, hands, bank, and deck composition match approved facts. |
| Turn phases | Partial | Strict roll→trade→build is present; turn-start victory check is missing. |
| Production | Pass | Settlement/city quantities, robber blocking, desert exclusion, and multiple entitlements are represented. Bank-shortage behavior remains explicitly unscored. |
| Domestic/maritime trade | Partial | Rates and bilateral legs are represented; offer enumeration leaks private holdings. |
| Building and stock | Pass | Costs, connectivity, distance rule, upgrades, and returned settlement stock are represented. |
| Longest Road/Largest Army | Pass | Thresholds, strict transfers, ties, blocking, and edge-simple road traversal align with approved facts. |
| Seven and robber | Pass | Resource-only discard totals, different robber hex, eligible victims, and random resource transfer are represented. |
| Development cards | Pass | Timing restriction, one-card allowance, deck contents, and principal effects are represented. |
| Information | Partial | Observations largely hide identities, but trade legal actions disclose exact opponent resources. |
| Scoring and terminal state | Partial | Scores are calculated, but turn-start victory and approved VP revelation are missing; first-road victory can crash. |
| Returns | Pass | Terminal winner/loser returns are internally consistent; no contrary packet rule was supplied. |

## Missing deterministic scenarios

- A player begins their turn with ten points and must win before rolling.
- The first Road Building road grants Longest Road and reaches ten points.
- A second Road Building road is impossible after the first; the phase should resume without mutating state merely by querying legal actions.
- Victory needing one hidden VP card versus multiple hidden VP cards, verifying minimum reveal in hand order.
- Buying a VP card that immediately establishes victory and reveals exactly that card.
- Trade-offer construction against opponents with different secret inventories, verifying that legal-action availability does not reveal identities or counts.
- Terminal observations where public score, revealed VP cards, winner, and private hand are mutually consistent.
- A non-active player at ten who becomes active after the current player ends their turn.

## Material questions for a human

- `legal_actions()` mutates the supplied state when Road Building has no legal placement (`_finish_road_building(d)` at lines 212–214). The packet does not explicitly define query purity. Should automatic completion occur inside the preceding action transition, or is mutation during legal-action enumeration an accepted interface convention?
- `render()` calculates scores with hidden VP cards included. The packet defines privacy for observations but does not expressly classify `render()` as public or private. If public, it also leaks hidden VP information.
- Bank-shortage allocation remains an expressly unscored source gap and should not be resolved from outside knowledge.

score: 0.64
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true