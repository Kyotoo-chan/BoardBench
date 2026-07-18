## 1. Assessment

**Score: 0.24 — confidence: high.**

The module models several base-game mechanics correctly, including ordered hands, compulsory first planting, optional second planting, same-type fields, clockwise rotation, and ordinary harvest protection. However, it implements the wrong source condition, uses the wrong phase-4 draw procedure, detects deck depletion too late, cannot resolve Ackerbohnen, exposes private information, restricts legal harvesting and trading, miscalculates Gartenbohne rewards, and can declare the wrong winner.

## 2. Findings

### Critical

1. **Third depletion is detected only on a later attempted draw, allowing extra play after the game should end.**

   - Canonical facts: `END-01`, `END-02`, `END-05`, `DECK-01`
   - Evidence type: `rule_quote` plus `human_decision`
   - Source: `RULES`, PDF pp. 9–10
   - Exact evidence:
     - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
     - Approved `END-05`: “If third depletion occurs during variant phase 4, stop immediately after the draw that empties it.”
   - Conflicting code: `Game._draw`, `Game._reveal`, and the `finish_building` transition.
   - Expected: Drawing the last card itself records depletion. Third depletion in phase 2 finishes phases 2–3 and then scores; third depletion in phase 4 terminates immediately.
   - Implemented: `_draw` increments `empty_deck_count` only when called while the deck is already empty. If a call pops the final card, depletion is not recorded. Even when phase 4 later increments the count to three, `finish_building` checks the count before drawing and then advances to another turn. Players can therefore plant and pass through additional phases after the prescribed end.

2. **Ties can produce the wrong winner.**

   - Canonical fact: `END-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p. 9
   - Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
   - Conflicting code: `Game._finalize` → `winner_order`; `Game.returns`.
   - Expected: Among players tied on coins, the player farthest clockwise from the original start player is the unique winner.
   - Implemented: `winner_order` sorts clockwise distance ascending, favoring the closest player. `returns` ignores the tiebreak entirely and awards `+1` to every player tied for the largest coin total.

### Major

3. **The module constructs the 104-card base game instead of the approved 129-card Ackerbohne condition.**

   - Canonical facts: `INV-03`, `INV-04`, `ACKER-01`–`ACKER-04`
   - Evidence types: `rule_quote`, `user_observation`, and `human_decision`
   - Sources and evidence:
     - `RULES`, PDF p. 10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.”
     - `COMPONENTS`, `/bohnen/9/anzahl_karten`: Weinbrandbohne `22`.
     - `COMPONENTS`, `/bohnen/11/anzahl_karten`: Ackerbohne `3`.
     - `RULES`, PDF p. 11: harvesting two Ackerbohnen grants a third field; harvesting three grants three coins.
   - Conflicting code: `BEANS`, `COUNTS`, `METERS`, `Game.initial_state`, two-field-only loops.
   - Expected: Eight base types plus 22 Weinbrandbohnen and three Ackerbohnen, totaling 129; Acker harvests can unlock a persistent third field or yield three coins.
   - Implemented: Only the eight base types are included. Every player is permanently represented by two fields, and neither special Acker harvest behavior nor Weinbrand rewards exist.

4. **Phase 4 gives three cards to the active player instead of one card to every player.**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p. 10
   - Exact evidence: “zieht jeder von euch eine Karte vom Nachziehstapel … der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting code: `finish_building` transition, `for _ in range(3): ... s.hands[s.active].append(b)`.
   - Expected: Each of four or five players draws exactly one card, beginning with the active player and continuing clockwise.
   - Implemented: The active player alone attempts to draw three cards; all other players draw none.

5. **Gartenbohne harvest rewards are one coin too low.**

   - Canonical fact: `GOLD-08`
   - Evidence type: `user_observation`
   - Source: `COMPONENTS`, JSON Pointer `/bohnen/7/ernte`
   - Exact evidence: `2 → 2` coins and `3 → 3` coins.
   - Conflicting code: `METERS["Gartenbohne"] = (2, 3, None, None)` interpreted by `Game._harvest`.
   - Expected: Two Gartenbohnen yield two coins; three or more yield three.
   - Implemented: The generic threshold position is treated as the award, so two yield one coin and three yield two.

6. **Trading is limited to one card for zero or one card, contradicting unequal-quantity trades.**

   - Canonical fact: `TRADE-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p. 5
   - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
   - Conflicting code: `Game.legal_actions` trade construction and the `accept_trade` transition.
   - Expected: Consensual exchanges may transfer differing nonempty quantities, including two-for-one examples.
   - Implemented: Every offer transfers exactly one active-player card and requests at most one target-player card. Only one-for-one and one-way single-card gifts are representable.

7. **Mandatory incoming cards must be planted in fixed FIFO order.**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p. 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting code: `Game.legal_actions` and `plant_incoming`, both using `s.incoming[owner][0]`.
   - Expected: Each recipient chooses the order of received and retained revealed cards, including any intervening legal harvest decisions.
   - Implemented: Only the first list element can be planted. Since order can determine which field must be harvested, this can materially change outcomes.

8. **Most players cannot exercise the approved right to harvest during another player’s turn.**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p. 7
   - Exact source evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting code: `Game.current_player` and `Game.legal_actions`.
   - Expected: Any owner may harvest between individual atomic steps, including during another player’s turn.
   - Implemented: Harvest actions are generated only for `current_player`: normally the active player, a pending trade target, or the selected build recipient. Other players have no harvest action.

9. **The public state interface exposes every ordered hand and the future deck.**

   - Canonical fact: `HAND-03` and the explicit executable observation convention
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p. 3
   - Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.” Approved convention: “State observations expose each player’s own whole ordered hand and only its count to opponents.”
   - Conflicting code: public `GameState.hands`, public `GameState.deck`, `initial_state`/`apply_action` returning that state, and `render` printing every hand.
   - Expected: A player sees their own ordered hand; opponents receive only hand counts. Future deck order is not observable.
   - Implemented: No player-specific observation method exists. Returned state exposes all hands and the full shuffled deck, while `render` explicitly prints all hands.

### Minor

10. **The start player is fixed to seat 0 and no persistent marker is modeled.**

   - Canonical fact: `SET-03`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p. 2
   - Evidence: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
   - Conflicting code: `GameState.active = 0`, no constructor start-player option, and tiebreak computation hard-coded relative to `0`.
   - Expected: A configured/chosen player acts first and retains the marker.
   - Implemented: Seat 0 is unconditionally assumed to be the start player.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup/player count | Partial | Correctly limits play to 4–5; start player fixed |
| Inventory | Incorrect | Base 104-card deck instead of selected 129-card deck |
| Ordered hands | Partial | Draws append and planting removes front; privacy absent |
| Phase 1 planting | Mostly correct | Mandatory first, optional second, forced harvest representable |
| Reveal | Partial | Two draws attempted; depletion timing is wrong |
| Trading | Incorrect | Consent exists, but quantity and gift directions are restricted |
| Mandatory planting | Partial | All incoming cards must be planted, but order is fixed |
| Phase 4 | Incorrect | Three active-player draws instead of one per player |
| Ordinary harvesting | Partial | Protection and most meters work; timing and Garten rewards fail |
| Acker/third field | Absent | No Acker cards, rewards, or third-field state |
| Deck recycling/end timing | Incorrect | Depletion recorded one draw too late |
| Final scoring | Partial | Fields harvested and hands ignored; tie winner incorrect |
| Returns | Incorrect on ties | Nonterminal zeros are correct |
| Elimination | Correct | No elimination mechanism |

## 4. Missing deterministic scenarios

- Initial deck composition asserts exactly 129 cards with 22 Weinbrandbohnen and three Ackerbohnen.
- Phase 4 with four and five players verifies one clockwise draw per player.
- Last-card draw tests for first, second, and third depletion.
- Third depletion on reveal draw one versus reveal draw two.
- Third depletion at each seat position during phase 4, ensuring no later player draws.
- Two Ackerbohnen with and without an existing third field.
- Three Ackerbohnen yielding exactly three coins.
- One Ackerbohne zero harvest subject to singleton protection.
- Persistence and ordinary use of an unlocked third field.
- Gartenbohne harvests at sizes one, two, three, and above.
- Two-for-one trade, unequal larger trade, and gift from an inactive player to the active player.
- Recipient-selected planting orders that lead to different forced harvests.
- Inactive-player harvest between atomic steps.
- Player-specific observations hiding opponent hand order and deck order.
- Final coin tie among multiple seat positions relative to a nonzero start player.
- Exact-deck-empty state after a pop, confirming immediate reshuffle or termination.

## 5. Material questions for a human

No material rulebook clarification is needed for the findings above; the approved facts decide them. One interface question remains: whether `GameState` is intended as trusted engine-internal state only. Even if so, the module still lacks the required player-specific observation interface, and `render` reveals all hands.

score: 0.24
confidence: high
critical_issues: 2
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true