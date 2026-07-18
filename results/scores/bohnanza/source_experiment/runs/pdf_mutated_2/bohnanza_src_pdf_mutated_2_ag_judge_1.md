score: 0.34  
confidence: high

The inventory, Bohnometer values, phase-1 planting, field protection, Ackerbohne rewards, final scoring, tie-break, and return values are substantially correct. However, third-depletion timing can change the winner, and several material action, phase, setup, and information rules are missing or contradicted.

## Findings

### Critical — depletion is detected one draw too late

- Canonical facts: `DECK-01`, `END-05`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.” and “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: `Game._draw_one`, `Game.apply_action` transition for `draw_to_hand`
- Expected: Depletion occurs when the last card is drawn. On the first two depletions, discard is immediately shuffled; on a phase-4 third depletion, the game ends immediately after that card, before another action or draw.
- Implemented: `_draw_one` increments `exhaustions` only when the deck is already empty before a draw. Popping the last card does not register depletion. If that card is the final phase-4 draw, another turn can begin and players may plant or trade before the next draw finally detects terminality. This can alter final fields, coins, and the winner. Delayed first/second reshuffles can also incorporate cards discarded after the actual depletion point, changing the future deck.

### Major — variant phase 4 deals the wrong number of cards to the wrong players

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting code: `finish_phase3` sets `draw_remaining = 3`; `draw_to_hand` always appends to `s.players[s.active].hand`
- Expected: Every player draws exactly one card, beginning with the active player and proceeding clockwise—four or five total draws.
- Implemented: Exactly three cards are drawn, all into the active player’s hand.

### Major — trades and gifts are unilateral and cannot express unequal atomic exchanges

- Canonical facts: `TRADE-04`, `TRADE-05`, `TRADE-07`
- Evidence type: `rule_quote`
- Sources and evidence:
  - `RULES`, PDF page 5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
  - `RULES`, PDF page 6: “Ziehe eine Karte erst aus der Hand, sobald der Handel auch wirklich zustande kommt. Denn beide Spieler müssen dem Handel zustimmen.”
  - `RULES`, PDF page 6: “Der beschenkte Mitspieler muss dem Geschenk aber zustimmen. Lehnt er ab, kommt der Handel nicht zustande.”
- Conflicting code: `Game.legal_actions` and `apply_action` branches `gift`/`trade`
- Expected: A proposal remains non-mutating until explicit acceptance; either participant may reject. Exchanges may contain unequal quantities.
- Implemented: The active controller selects a `gift` or `trade` that transfers cards immediately. It can take a card from an inactive player without that player acting, and `trade` supports only one-for-one exchange. Sequential gifts cannot reproduce an atomic unequal trade because each transfer is immediately committed.

### Major — mandatory planting order is fixed instead of chosen

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions` selects `bean = q.pending[0]`; `plant_pending` always removes `pending.pop(0)`
- Expected: Each recipient may select any pending received/revealed card as the next card planted, including choosing legal harvests between individual plantings.
- Implemented: Pending cards must be planted in acquisition/list order.

### Major — voluntary harvesting between atomic steps is absent

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code: `Game.legal_actions`
- Expected: An owner may voluntarily harvest between individual game steps, including during another player’s turn, subject to singleton protection.
- Implemented: `harvest` is offered only when the currently mandatory card has no planting destination. Legal voluntary harvests, including those by inactive players, are unavailable.

This is an adjudication-dependent deviation: the approved temporal decision limits “jederzeit” to boundaries between atomic operations.

### Major — private hand information is exposed

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
- Approved decision: Owners observe their full ordered hand; opponents observe only its count unless information is voluntarily communicated.
- Conflicting code: `Game.render`; no player-relative observation method exists
- Expected: Player-facing observations hide opponents’ card identities and order.
- Implemented: `render` prints every player’s complete hand. The module supplies no restricted observation surface.

This privacy scope comes from the approved human decision rather than an independently complete printed-rule statement.

### Major — the start player cannot be configured or chosen

- Canonical fact: `SET-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 2
- Exact evidence: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
- Conflicting code: `Game.__init__`, `GameState.start_player`, `GameState.active`, `initial_state`
- Expected: One configured or chosen start player acts first and retains the marker.
- Implemented: Both `active` and `start_player` are always initialized to player 0, with no setup choice or constructor parameter. This also fixes the tie-break reference seat.

## Rule-area coverage

| Rule area | Status | Assessment |
|---|---|---|
| Player count and deck inventory | Pass | Correct 4–5 restriction and 129-card selected deck |
| Setup | Partial | Five-card hands correct; start player fixed |
| Hand order | Partial | Front planting and append behavior correct; privacy missing |
| Phase 1 planting | Pass | Mandatory first, optional second, no third |
| Reveal | Partial | Two-card flow present; depletion boundary wrong |
| Trading and gifts | Fail | No consent protocol or unequal atomic trades |
| Phase 3 planting | Partial | All pending cards planted, but fixed order |
| Phase 4 drawing | Fail | Three cards all go to active player |
| Harvest and payouts | Partial | Payouts, protection, and Acker rules correct; voluntary timing absent |
| End and scoring | Partial | Final harvest and tie-break correct; terminal trigger delayed |
| Returns | Pass | Nonterminal zero and terminal winner-based values permitted |

## Missing deterministic scenarios

- Third depletion caused by the last required phase-4 draw; assert immediate terminality before the next phase-1 action.
- First/second depletion on the exact last card; assert immediate reshuffle before later trade/plant discards occur.
- Four-player and five-player phase 4; assert one clockwise draw per player.
- Proposed trade rejection; assert no card moves before acceptance.
- Unequal atomic trade such as two cards for one.
- Gift rejection, including an attempted inactive-player-to-active gift.
- Three pending beans where choosing a non-front card first avoids or changes a harvest.
- Voluntary harvest by the active player and by an inactive player between atomic steps.
- Player-relative observations showing own ordered hand but only opponent hand counts.
- Nonzero configured start player, including a tied final score resolved relative to that seat.

## Material questions for a human

No additional publisher-rule clarification is needed for the scored contradictions. Implementation design still needs two choices:

- Whether start-player selection is a constructor parameter or an explicit setup action.
- How trade proposal ownership and recipient acceptance are represented in the turn/action API.

The packet does not specify an inter-player ordering when several players have pending cards in phase 3. That is a question rather than a penalty; it does not remove each player’s required choice of their own planting order.

score: 0.34
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true