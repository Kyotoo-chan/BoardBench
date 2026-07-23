## Assessment

`score: 0.58` — `confidence: high`

The module covers most fixed setup, production, building, robber, development-card, scoring, and trade mechanics. However, it has one reproducible winning-action crash, can miss a required turn-start victory, and leaks private resource identities through legal-action enumeration.

## Findings

### Critical — Winning via a free Road Building road crashes

- Canonical fact ID: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 2
- Exact evidence: “Check victory after every completed atomic action or committed subaction… This includes turn start before rolling and the first free road of Road Building.”
- Conflicting symbols: `Game.apply_action`, `place_free_road`; `_place_road`; `_victory`
- Expected: Each free road is placed atomically, Longest Road is recalculated, and a resulting ten-point victory terminates successfully.
- Implemented: `_place_road()` calls `_victory()`, which sets `pending = None` when the road wins. Control then returns to `apply_action`, which executes `d["pending"]["remaining"] -= 1`. This dereferences `None` and raises instead of returning the terminal state. It affects a winning first or second free road.

### Critical — Turn-start victory is not checked

- Canonical fact IDs: `CAT-D-WIN`, `CAT-WIN-01`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 2
- Exact evidence: “This includes turn start before rolling.”
- Supporting rule quote:
  - Source ID: `CATAN22-RULES`
  - Locator: PDF p. 4
  - Exact evidence: “Um zu gewinnen, muss ein Spieler an der Reihe sein und in seinem Zug mindestens 10 Siegpunkte erreichen/besitzen.”
- Conflicting symbols: `Game.apply_action`, `end_turn`; `Game.legal_actions`, `roll` phase
- Expected: After the next player becomes active, victory is immediately checked before rolling.
- Implemented: `end_turn` changes the active player and directly installs the `roll` phase without calling `_victory`. `legal_actions` then permits rolling. This matters when a non-active player reaches ten through an out-of-turn Longest Road reassignment and later becomes active.

### Major — Domestic-trade actions reveal opponents’ resource identities

- Canonical fact ID: `CAT-INFO-01`
- Evidence type: `rule_quote`
- Source ID: `CATAN22-RULES`
- Stable locator: PDF p. 2
- Exact evidence: “Seine Rohstoffkarten hält jeder Spieler verdeckt in der Hand.”
- Conflicting symbol: `Game.legal_actions`, `trade_offer` branch
- Expected: Opponents’ resource identities remain private.
- Implemented: For each partner and resource, an `add_trade_item(... direction="take", resource=r)` action is offered only while that partner possesses another card of `r`. By repeatedly examining and extending the offer, the active player can determine every opponent’s exact resource composition and quantities.

### Major — Winning victory-point cards are never revealed

- Canonical fact IDs: `CAT-D-VP-REVEAL`, `CAT-INFO-01`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 8
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten.”
- Supporting rule quote:
  - Source ID: `CATAN22-RULES`
  - Locator: PDF p. 4
  - Exact evidence: “Karten mit Siegpunkten werden grundsätzlich geheim gehalten. Sie werden erst aufgedeckt, wenn ein Spieler insgesamt 10 Siegpunkte erreicht hat.”
- Conflicting symbols: `_score`, `_victory`, `observation_to_data`
- Expected: Victory detection publicly reveals the minimum necessary hidden cards in hand order.
- Implemented: `_score(..., include_hidden=True)` silently counts every hidden victory-point card, but `_victory` never marks or moves any card as revealed. `public_scores` continues to exclude them, and opponent observations expose only the unchanged face-down count.

No separate minor findings.

## Rule-area coverage

| Area | Coverage | Result |
|---|---|---|
| Fixed setup and inventory | Terrain, numbers, pieces, hands, bank, deck | Consistent with approved facts |
| Turn phases | Strict roll → trade → build | Mostly correct; turn-start win missing |
| Production | Settlements/cities, robber blocking, desert | Consistent; shortage behavior properly left unscored |
| Trading | Domestic, maritime, harbors | Mechanics mostly consistent; private-hand leak |
| Building and graph legality | Costs, stock, distance, connections | Consistent |
| Longest Road / Largest Army | Trail calculation, ties, interruption | Consistent on static inspection |
| Seven and robber | Discard amount, movement, victim choice, theft | Consistent with approved decision |
| Development cards | Timing and effects | Mostly consistent; winning free-road crash |
| Private/public information | Observation redaction and counts | Material trade leak and missing VP reveal |
| Terminal conditions | Active-player threshold | Two critical defects |
| Returns | Winner `+1`, others `-1` | Internally consistent once terminal state exists |

## Missing deterministic scenarios

- Road Building’s first free road gains Longest Road and reaches ten.
- Road Building’s second free road reaches ten.
- Exactly one free road is feasible, followed by automatic subphase completion.
- A non-active player reaches ten through Longest Road reassignment, then becomes active.
- Trade-offer enumeration against every possible hidden resource composition.
- Victory with multiple hidden VP cards, verifying minimal reveal and hand order.
- Terminal observations showing revealed VP cards and the complete public winning score.
- Repeated `legal_actions` calls during an exhausted Road Building subphase, checking whether querying mutates state.

## Material questions for a human

- Must `legal_actions` be observationally pure? In an exhausted `road_building` phase it calls `_finish_road_building(d)` and mutates the supplied state. The approved register does not explicitly define query purity, so this is not scored.
- Is partner acceptance represented outside this module? The active player can unilaterally commit a domestic trade once quantities are entered. `CAT-D-TRADE` describes an “agreement” but does not specify a separate acceptance transition, so this is not penalized.

score: 0.58
confidence: high
critical_issues: 2
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true