## Assessment

Score: **0.58**  
Confidence: **high**

The module statically covers most of the fixed setup, ordinary roll/trade/build flow, production, robber movement, construction, development effects, scoring, and observations. However, a valid Road Building win can crash, and several approved edge cases involving road stock, turn-start victory, multileg trading, and victory-point disclosure are contradicted.

## Findings

### Critical — Winning with the first Road Building road crashes

- Canonical facts: `CAT-D-WIN`, `CAT-D-ROAD-CARD`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” items 2 and 5
- Exact evidence:
  - “Check victory after every completed atomic action or committed subaction… This includes … the first free road of Road Building.”
  - “Road Building places the maximum feasible number up to two, sequentially. … Re-evaluate legality and victory after each road.”
- Conflicting transition: `apply_action("place_free_road")`, `_place_road()`, `_victory()`, lines 316–318 and 413–445.
- Expected: If the first free road grants Longest Road and brings the player to ten points, that road commits and the game immediately terminates.
- Implemented: `_place_road()` calls `_victory()`, which sets `pending=None`. Control returns to `apply_action`, which immediately executes `d["pending"]["remaining"] -= 1`, indexing `None` and raising an exception. The winning successor state is not returned.

### Major — Road Building can create a second road with no road piece available

- Canonical facts: `CAT-BUILD-03`, `CAT-D-ROAD-CARD`
- Evidence types: `rule_quote`, `human_decision`
- Source ID: `CATAN22-ALMANAC`
- Stable locator: PDF p. 6; approved decision 5
- Exact evidence:
  - “Jeder Spieler verfügt über 15 Straßen, 5 Siedlungen und 4 Städte.”
  - “Road Building places the maximum feasible number up to two… otherwise place exactly the feasible number.”
- Conflicting symbols: `_dev_actions()`, `legal_actions()` road-building branch, `_place_road()`, lines 187–188, 212–214, and 413–415.
- Expected: Physical stock determines feasibility. With one road piece remaining, Road Building places at most one road.
- Implemented: Playing the card requires only `pieces["roads"] > 0`. After placing the sole remaining piece, the `road_building` legal-action branch does not recheck stock and can offer another free road. Placing it decrements stock to `-1`.

### Major — Victory is not checked at turn start

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 2
- Exact evidence: “Check victory after every completed atomic action or committed subaction; if the active player then has at least ten, terminate immediately. This includes turn start before rolling…”
- Conflicting transition: `apply_action("end_turn")`, lines 328–331.
- Expected: When the next player becomes active, the module checks their complete score before offering a roll.
- Implemented: Turn transfer directly enters `phase="roll"` without calling `_victory()`. A player who reached ten while inactive—for example through a Longest Road reassignment—can be required to roll and may finish the turn without ever receiving the required immediate win.

### Major — Atomic multileg trades cannot reuse a resource received within the same agreement

- Canonical fact: `CAT-D-TRADE`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 7
- Exact evidence: “One committed domestic trade may contain several positive bilateral legs… The canonical interface builds the offer one resource at a time in a finite `trade_offer` subphase, then commits every leg atomically…”
- Conflicting symbols: trade-offer generation, `_trade_committable()`, and `_commit_trade()`, lines 220–229 and 389–412.
- Expected: The complete approved atomic combination is evaluated as a whole, including the permitted five-card combination that retrieves and reuses one of its own transferred components.
- Implemented: Outgoing quantities are capped against the active player’s pre-trade hand, both while building the offer and when committing it. An incoming component from another leg cannot satisfy an outgoing leg, so the approved combination is unavailable.

### Major — Winning victory-point cards are never revealed

- Canonical fact: `CAT-D-VP-REVEAL`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: “Approved human decisions,” item 8
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten…”
- Conflicting symbols: `_score()`, `_victory()`, and `observation_to_data()`, lines 155–163, 441–443, and 501–525.
- Expected: Victory detection reveals exactly the minimum necessary hidden victory-point cards, making those cards and the established score public.
- Implemented: `_score()` silently counts every hidden victory-point card, while `_victory()` only sets terminal fields. No cards are revealed or moved, and `public_scores` continues to exclude all hidden victory points even in the terminal observation.

### Minor — Knight victory leaves a contradictory terminal phase

`play_knight` calls `_victory()` and then overwrites the resulting `phase="terminal"` and cleared pending state with `phase="robber_move"` and a robber pending action. `terminal=True` prevents further legal actions, so returns still work, but the serialized terminal state reports an unfinished robber transition.

### Minor — Road Building completion depends on a mutating query

If fewer than two roads are feasible, the action result remains in `road_building`. A subsequent call to `legal_actions()` invokes `_finish_road_building()` on the supplied state itself. Thus a query mutates game state and performs a required phase transition rather than the preceding committed action returning the completed successor.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Fixed setup and inventory | Covered | Layout, initial pieces, hands, bank counts, deck composition, and robber location match the approved register. |
| Turn phases | Partial | Strict roll → trade → build is modeled; turn-start victory is missing. |
| Production | Covered | Settlements/cities, multiple entitlements, desert, and robber blocking are represented. Bank shortages are appropriately unscored. |
| Seven and robber | Covered | Discards, forced different hex, eligible-victim choice, and random resource theft are modeled. |
| Domestic/maritime trade | Partial | Rates and active-player restriction work; approved atomic resource reuse does not. |
| Building legality and stock | Partial | Ordinary construction is sound; Road Building can exceed road stock. |
| Longest Road/Largest Army | Covered | Edge-simple trail logic, blocking, minimums, strict transfer, and holder ties are represented. |
| Development cards | Partial | Effects and one-card timing are mostly correct; Road Building has terminal/stock defects. |
| Private information | Mostly covered | Player observations hide identities and expose approved counts; victory-point revelation is absent. |
| Terminal conditions/returns | Partial | Ordinary action-triggered wins return `+1/-1`; first-road wins can crash and turn-start wins are missed. |
| Serialization/action validation | Covered for normal states | No rule contradiction identified from static inspection. |

## Missing deterministic scenarios

- First Road Building road grants Longest Road and the tenth point.
- Road Building with exactly one physical road piece remaining.
- Road Building where only one legal placement remains after the first road.
- Player begins a turn already at ten because a special card changed ownership while they were inactive.
- Atomic multileg trade that receives and reuses one component.
- Win requiring one hidden victory-point card versus multiple hidden cards, verifying minimum ordered revelation.
- Knight grants Largest Army and the tenth point, verifying a coherent terminal phase.
- Serialization immediately after a one-road Road Building resolution, before any `legal_actions()` query.
- Longest Road ties with and without the incumbent holder.
- Seven with several eligible victims, empty adjacent opponents, and privately committed discards.

## Material questions for a human

- Is `render()` intended as a public/player-facing view or a privileged debugging view? It uses `_score(..., include_hidden=True)` for every player, which can disclose hidden victory-point totals. If public, this conflicts with `CAT-INFO-01`; the packet does not explicitly classify the render channel.
- Should raw `state_to_data()` be treated as trusted engine serialization only? It exposes all private identities, whereas the player-specific observation path correctly redacts them.

score: 0.58
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true