Score: **0.34**, confidence: **high**. The module models inventory, field planting, yield tables, Ackerbohne rewards, and hand order reasonably well. However, final scoring can select the wrong winner, while several central variant, timing, trade, and information rules are contradicted or absent.

## Findings

### Critical

1. **Terminal scoring counts hands and omits final field harvests**

   - Canonical fact: `END-03`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr.”
   - Conflicting symbol: `Game.returns`
   - Expected: At game end, harvest every field using its normal yield; cards remaining in hands score zero.
   - Implemented: `scores = state.coins[p] + len(state.hands[p])`. Unharvested fields contribute nothing, while every hand card incorrectly contributes one point.
   - Impact: This directly and commonly produces incorrect scores and winners.

### Major

2. **Variant phase 4 gives three cards to the active player**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel … der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting symbols: `legal_actions` action `("draw_three",)`; `apply_action` branch `draw_three`
   - Expected: Each player draws exactly one card, beginning with the active player and proceeding clockwise; each card appends to that recipient’s hand.
   - Implemented: Three cards are drawn, all into `hands[s.active]`.
   - Impact: Materially changes private information, hand sizes, deck depletion, and subsequent turns.

3. **Depletion is detected only on an attempted draw after the deck became empty**

   - Canonical facts and evidence:
     - `END-01`; `rule_quote`; `RULES`, page 9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - `END-05`; `human_decision`; `RULES`, page 9: “endet, sobald”; approved expectation: a third depletion during phase 4 is terminal immediately after the draw that empties the pile.
     - `END-02`; `rule_quote`; `RULES`, page 9: “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende.”
   - Conflicting symbols: `Game._draw`, `reveal_two`, and `draw_three`
   - Expected: Register depletion on the draw that removes the final card. In phase 2, finish phases 2–3 and skip phase 4; in phase 4, terminate immediately before another player draws.
   - Implemented: `_draw` checks emptiness only before `pop()`. If the final card is consumed by the last iteration of a draw loop, depletion is not registered until a later action. Phase-2 depletion also requires a dummy `draw_three` action after phase 3 before becoming terminal.
   - Impact: Turns or actions can continue past the prescribed endpoint, affecting scoring and winner determination.

4. **Trades cannot atomically exchange unequal quantities**

   - Canonical fact: `TRADE-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 5
   - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
   - Conflicting symbols: `propose_trade` generation and `accept`
   - Expected: A consensual proposal may transfer differing nonzero numbers of cards atomically.
   - Implemented: Every trade selects exactly one active-player card and one target-player card. Separate gifts cannot reproduce the consent and atomicity of a multi-card exchange.
   - Impact: A material class of legal negotiations is unavailable.

5. **Mandatory planting order is fixed by proposal resolution rather than chosen by each recipient**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbols: `GameState.planting`, `accept`, `finish_trading`, and `plant_trade`
   - Expected: Each player chooses the order of their received cards and can make necessary legal harvest choices between them.
   - Implemented: Cards enter one global FIFO queue. Only `planting[0]` can be planted, so neither recipient nor active player can select among their pending beans.
   - Impact: Planting order can determine which field must be harvested and therefore how many coins are earned.

6. **Owners cannot exercise the approved between-step harvesting right during another player’s turn**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Approved boundary: Harvesting is allowed between individual game steps, including during another turn, but not inside an atomic draw or transfer.
   - Conflicting symbols: `legal_actions`, `_harvest_actions`, and `controller`
   - Expected: At eligible boundaries, any field owner can become the acting controller for an explicit harvest.
   - Implemented: Harvest actions are offered only to the current controller during hand planting, or to the owner of the first queued mandatory planting card. Other players cannot harvest during another player’s reveal, trade, or between planting steps.
   - Impact: A significant strategic action and timing right is absent.

7. **No compliant player-specific observation is provided**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
   - Approved expectation: The owner sees their entire ordered hand; opponents see only its count unless voluntarily communicated.
   - Conflicting symbols: returned `GameState`, `render`
   - Expected: A player observation exposes that player’s ordered hand and only opponent hand counts, without exposing the hidden deck.
   - Implemented: No player-specific observation method exists. The returned state contains every hand and the complete ordered deck, while `render` exposes only hand sizes—even to the owner.
   - Impact: Depending on how callers consume state, the module either leaks all private information or withholds the acting player’s own cards.

No minor findings.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count and fields | Pass | Correct 4–5-player condition and two starting fields |
| Deck inventory | Pass | Correct 129-card, ten-type composition |
| Initial hands/order | Pass | Five cards, append draws, front-card planting |
| Turn order and phases 1–2 | Mostly pass | Clockwise turns, mandatory/optional planting, two reveals |
| Trading | Fail | Only atomic 1-for-1 trades or one-card gifts |
| Mandatory planting | Fail | All cards are planted, but order is fixed |
| Variant phase 4 | Fail | Active player draws three instead of everyone drawing one |
| Normal harvest/yields | Pass | Protection and supplied meters are correctly represented |
| Harvest timing | Fail | Inactive-owner harvesting is unavailable |
| Ackerbohne | Pass | One/two/three-card outcomes match approved decisions |
| Reshuffling | Partial | First/second reshuffle logic exists; depletion timing is late |
| End conditions | Fail | Late detection and dummy phase-4 transition |
| Final scoring/returns | Fail | Hands counted and fields not harvested |
| Private information | Fail | No compliant player observation boundary |

## Missing deterministic scenarios

- Every player receives exactly one phase-4 draw in clockwise order.
- Third depletion on each possible phase-4 recipient.
- Last card drawn as the final iteration of a draw action.
- Third depletion during either phase-2 reveal, followed by phases 2–3 but no phase 4.
- Terminal scoring with valuable fields and nonempty hands.
- A final harvest that changes the winner or tie-break participants.
- Atomic two-for-one and one-for-two trades.
- Recipient-selected planting order where different orders force different harvests.
- An inactive player harvesting between another player’s planting steps.
- Per-player observations proving own-hand visibility, opponent-hand hiding, and deck secrecy.
- First/second depletion with an owed draw continuing after discard reshuffle.

## Material questions for a human

- Is player index `0` explicitly intended to represent the already chosen start player? If so, the fixed start seat is harmless; otherwise the setup API lacks start-player configuration.
- Is an external trusted observation layer expected but omitted from this packet? No such layer appears in `implementation.py`; if one exists elsewhere, the information finding should be reassessed against it.

```text
score: 0.34
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```