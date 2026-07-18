Score: **0.40**, confidence: **high**. The module implements much of the basic turn skeleton, ordered hands, ordinary planting, consensual trades, normal harvest yields, and winner returns. However, seven material contradictions affect mandatory planting, harvesting access, gifts, depletion timing, Ackerbohne rewards, Weinbrandbohne rewards, and terminal score observability.

## Findings

### Major 1 — Cards received by inactive players are never mandatorily planted

- Canonical fact: `P3-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen. Als aktiver Spieler musst du auch jede aufgedeckte Karte anbauen, die du nicht gehandelt hast.”
- Conflicting symbols: `current_player`, `legal_actions` branch `plant_incoming`, `finish_incoming`
- Expected: Every player plants all received cards, choosing their own order and harvesting as necessary. The active player also plants retained reveals.
- Implemented: `plant_incoming` always assigns control to `s.active`. Once the active player’s `incoming` is empty, `finish_incoming` advances directly to `draw_each`. Cards in other players’ `incoming` lists remain unplanted, including cards just received in accepted trades.

This materially breaks a common trade outcome and can also cause received cards to disappear from final scoring.

### Major 2 — Deck depletion is detected one draw too late

- Canonical facts: `DECK-01`, `END-02`, `END-05`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren, spielt ihr die 2. und die 3. Phase noch zu Ende.”
- Conflicting symbols: `_draw`, `reveal_two`, `draw_one`
- Expected:
  - Drawing the last card causes depletion immediately.
  - First and second depletion immediately reshuffle before any remaining owed draw.
  - Third depletion on the second reveal still finishes phases 2–3 and skips phase 4.
  - Third depletion during phase 4 terminates immediately after the draw that empties the pile.
- Implemented: `_draw` increments `empty_count` only when called while `s.deck` is already empty. If a draw pops the last card, depletion remains unnoticed until another `draw_one` or `_draw` call. This can:
  - wrongly enter phase 4 after third depletion during reveal;
  - offer another player a phase-4 draw action after the game should already have ended;
  - allow intervening harvests to add cards to the discard before a first/second-depletion reshuffle.

### Major 3 — Harvesting two Ackerbohnen incorrectly awards two coins

- Canonical fact: `ACKER-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 11
- Exact evidence: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld. … Die geernteten Ackerbohnen legst du auf den Ablagestapel.”
- Conflicting symbol: `_harvest`, branch `bean == "Ackerbohne"`
- Expected: Exactly two Ackerbohnen unlock the third field if absent; both cards go to the discard and award zero coins.
- Implemented: `value` becomes `2`, `p.coins` increases by two, and `cards[value:]` is empty, so neither card is discarded. The third field is also unlocked.

This directly alters scores and card circulation.

### Major 4 — Weinbrandbohne harvest thresholds are wrong

- Canonical fact: `GOLD-09`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/9/ernte`
- Exact evidence: thresholds `4→1, 7→2, 9→3, 11→4`
- Conflicting symbol: `BEANS["Weinbrandbohne"]`
- Expected: Zero below four; then 1/2/3/4 coins at 4/7/9/11 or more.
- Implemented: `((2, 1), (4, 2), (6, 3), (8, 4))`.

Every Weinbrandbohne harvest band is materially overstated.

### Major 5 — Inactive owners cannot exercise the anytime-harvest rule

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbols: `legal_actions`, `_harvest_actions`, `current_player`
- Expected: Any owner may harvest between atomic steps, including during another player’s turn.
- Implemented: `legal_actions` generates harvests only for `current_player(s)`, normally the active player. During offer response or phase-4 drawing it merely shifts that privilege to the responding/drawing player; other owners still cannot harvest.

### Major 6 — An inactive player cannot give a card to the active player as a gift

- Canonical fact: `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting symbols: `Offer`, `legal_actions` branch `trade`, `submit_offer`
- Expected: A nonempty one-way transfer is legal with the recipient’s consent.
- Implemented: A transfer from the target’s hand to the active player is represented by `request_hand` with no active-player cards offered. `submit_offer` is exposed only when `give_hand` or `give_market` is nonempty, so this valid one-way gift cannot be submitted.

Active-to-inactive gifts are supported; the reverse direction is not.

### Major 7 — Terminal raw coin totals are not observable

- Canonical fact: `END-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr.”
- Conflicting symbols: `returns`, `render`, terminal `GameState`
- Expected: All fields are finally harvested, and the resulting raw coin totals remain observable, as required by the packet’s executable convention.
- Implemented: `returns` deep-copies the terminal state and harvests only the copy. It returns the correct winner vector relative to that copied score calculation, but the actual terminal state and `render` still show pre-final coins and unharvested fields.

This also obscures the score basis used to select the winner.

No critical or minor findings were established.

## Coverage

| Rule area | Coverage | Result |
|---|---|---|
| Setup and inventory | `SET-01–03`, `INV-01–05`, `HAND-01–03` | Correct 4–5-player, 129-card deck and ordered five-card deal; start player is implicitly fixed to seat 0 |
| Turn flow | `TURN-01–02`, `P1-01–04` | Four-phase clockwise skeleton and phase-1 limits implemented |
| Field planting | `FIELD-01`, `P3-01–02` | Same-type fields and selectable incoming order work; inactive recipients are skipped |
| Reveal and trade | `P2-01`, `TRADE-01–07` | Public market state and consensual atomic exchanges mostly represented; reverse-direction gift absent |
| Draw and reshuffle | `P4-01`, `DECK-01` | One draw per player implemented; depletion timing incorrect |
| Harvesting | `HARV-01–03` | Protection and normal harvest mechanics work; out-of-turn access is incomplete |
| Harvest values | `GOLD-01–09` | Base types correct; Weinbrandbohne wrong |
| Ackerbohne | `ACKER-01–04` | One- and three-card outcomes broadly align; two-card harvest wrongly awards coins |
| End and returns | `END-01–06` | Tie-break and simulated final harvest exist; timing and score observability are wrong |
| Private/public information | `HAND-03`, `P2-01` | Acting hand is masked appropriately in `render`; public market/offer rendering is unclear |

## Missing deterministic scenarios

1. Trade cards to two different inactive recipients and require each recipient to plant them before phase 4.
2. Harvest exactly two Ackerbohnen with no third field: assert field unlock, zero coins, and both cards discarded.
3. Exercise Weinbrandbohne harvests at 2, 4, 7, 9, and 11 cards.
4. Let an inactive owner harvest legally between two atomic actions on another player’s turn.
5. Submit and accept a gift from an inactive player’s hand to the active player with no return card.
6. Draw the exact last card on:
   - first/second depletion with another draw owed;
   - the second reveal on third depletion;
   - a phase-4 draw on third depletion.
7. At terminal state, verify final harvested coin totals and emptied fields are observable and agree with `returns`.
8. Combine a trade with mandatory forced harvesting by an inactive recipient before planting.
9. Verify tie-breaking after final harvest using observable raw scores.

## Material questions for a human

- Is `render` the authoritative observation interface? It omits the public market and pending offer details. If consumers cannot inspect appropriately filtered state, this is an additional information defect.
- Is seat 0 intentionally the configured start player, or must callers be able to choose another seat? `SET-03` permits configuration, but the intended API is not specified.
- Is raw `GameState` private to the engine? Direct access exposes every ordered hand, while `render` masks them.

These interface questions were not scored as additional findings; the approved gameplay facts already decide the seven contradictions above.

score: 0.40
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true