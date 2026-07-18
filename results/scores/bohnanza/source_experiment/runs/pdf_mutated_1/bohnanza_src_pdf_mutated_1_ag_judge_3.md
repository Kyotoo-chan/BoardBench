## 1. Score

`score: 0.34` — `confidence: high`

The implementation gets deck composition, initial hands/fields, ordered-hand planting, bean meters, field protection, and most Ackerbohne rewards right. However, phase 4 is fundamentally misimplemented, terminal scoring can select the wrong winner, and several material trade, planting-order, timing, and information rules are absent.

## 2. Findings

### Critical

1. Terminal scoring counts hands and never performs the required final harvest.

   - Canonical fact: `END-03`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr.”
   - Conflicting code: `Game.returns`; terminal branch of `Game.apply_action`
   - Expected: At termination, harvest every field, count the resulting coin cards, and give hand cards no value.
   - Implemented: `returns()` calculates `coins[p] + len(hands[p])`; fields are never finally harvested.
   - Impact: Both omitted field proceeds and improperly counted hands can fundamentally change scores and the winner.

### Major

2. Variant phase 4 gives three cards to the active player instead of one card to every player.

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting code: `legal_actions()` exposes `("draw_three",)`; `apply_action()` draws three times into `s.hands[s.active]`.
   - Expected: Each of the four or five players draws one card, active player first and then clockwise.
   - Implemented: Only the active player draws, receiving up to three cards.

3. Unequal multi-card trades cannot be proposed or accepted atomically.

   - Canonical facts: `TRADE-04`, `TRADE-05`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF pages 5–6
   - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.” Also: “Beide Spieler müssen dem Handel zustimmen.”
   - Conflicting code: `propose_trade`, `propose_gift`, `accept`
   - Expected: A consensual atomic exchange may contain unequal nonzero quantities, such as two cards for one.
   - Implemented: A proposal contains exactly one active-player card and, for a trade, exactly one target-player card. Sequential one-card proposals are not equivalent because each resolves independently and received cards cannot be retraded.

4. Mandatory planting order is dictated by trade chronology.

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting code: `s.planting`, `accept`, `finish_trading`, `plant_trade`
   - Expected: Each recipient chooses the order in which their received cards are planted, including choosing when a necessary harvest occurs between cards.
   - Implemented: Cards are appended to a single queue and only `s.planting[0]` may be planted. The owner cannot select another owned pending card first.

5. Players cannot harvest during another player’s turn or in most between-action windows.

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact source evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Approved boundary: An owner may harvest between individual game steps, including during another player’s turn, but not inside an executing atomic draw or transfer.
   - Conflicting code: `_harvest_actions`, `legal_actions`, `controller`
   - Expected: Between atomic steps, each player with a legal field may choose to harvest it.
   - Implemented: Harvest actions are only generated for `s.controller`, and only in hand-planting or `plant_trades` phases. Inactive players get no such action.

6. Deck depletion is detected on a later draw attempt rather than when the final card is drawn.

   - Canonical fact: `END-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
   - Conflicting code: `_draw`
   - Expected: Depletion occurs when a draw removes the pile’s final card. On the third depletion, the appropriate phase-2 or phase-4 end boundary applies immediately.
   - Implemented: `empty_count` increments only when `_draw()` begins with an already-empty deck. If the last owed draw empties the pile, depletion is not noticed until a later action. This can improperly begin another phase or turn.

7. No player-relative observation satisfies the approved private-information convention.

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
   - Approved boundary: An owner observes their complete ordered hand; opponents observe only its count.
   - Conflicting code: `GameState.hands`, `GameState.deck`, `render`
   - Expected: Player-relative observations show the requesting player their hand, hide other hands, and hide the ordered draw pile.
   - Implemented: The state object exposes every hand and the complete ordered deck, while `render()` shows only hand sizes and therefore does not show even the controller’s own ordered hand.

### Questions

8. Is assigning seat `0` implicitly considered configuring the start player?

   `initial_state()` always sets `active=0`, and there is no start-player parameter or marker. This may be an acceptable seat-assignment convention, but the packet does not specify the module interface closely enough to penalize it. If start player must be selectable independently of seat numbering, `SET-03` and the `END-04` tie-break need additional state.

9. Which public API is intended to enforce observations?

   The approved facts decide what each player may observe, but not whether this must be implemented through `observation(player)`, filtered state copies, or another wrapper. The current module supplies no compliant route.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count/setup | Mostly covered | Correct 4–5 players, five cards, two fields; start selection is implicit |
| Inventory | Covered | Correct ten types and 129 cards |
| Hand order | Partly covered | Front planting and append behavior correct; observation boundary absent |
| Phase 1 planting | Covered | Mandatory first, optional second, homogeneous fields |
| Reveal | Mostly covered | Two reveals; exact depletion timing is wrong |
| Trading | Material gaps | Active-player participation works; unequal atomic bundles unsupported |
| Phase 3 planting | Material gap | Planting is mandatory, but order is forced |
| Phase 4 draw | Contradicted | Three to active instead of one to each player |
| Harvest values/protection | Covered | Normal meters and singleton protection match approved facts |
| Harvest timing | Material gap | Inactive/between-step harvesting unavailable |
| Ackerbohne | Covered | One, two, and three-card outcomes align with approved decisions |
| Depletion/reshuffle | Partly covered | Reshuffle exists; depletion event occurs too late |
| End scoring/winner | Contradicted | No final harvest; hands incorrectly score |
| Returns | Partly covered | Zero nonterminal and winner returns are shaped correctly, but use wrong scores |

## 4. Missing deterministic scenarios

- Terminal state where final field harvest and hand-card counting produce different winners.
- Four- and five-player phase-4 distribution, verifying one clockwise draw per player.
- Third depletion on the last phase-2 reveal and on each seat’s phase-4 draw.
- Accepted and rejected atomic two-for-one trades.
- Planting multiple received cards in either chosen order, with different forced-harvest consequences.
- Legal harvest by an inactive player between two atomic actions.
- Player-relative observations: own ordered hand visible, opponents’ hands and deck order hidden.
- Start-player/tie-break scenario if nonzero starting seats must be supported.
- Ackerbohne harvests of one, two with/without field 3, and exactly three.

## 5. Material questions for a human

- Is seat numbering permitted to encode the chosen start player, or must the constructor/state expose an explicit start-player choice?
- What observation method should evaluators call to obtain the approved player-relative information?
- Should asynchronous harvest opportunities be represented by temporarily transferring control, or through a separate interrupt-action mechanism?

score: 0.34
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true