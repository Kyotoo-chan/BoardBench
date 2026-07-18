Score: **0.38**, confidence: **high**. Setup, ordered hands, basic four-phase structure, normal harvest protection, most bean values, clockwise turns, and winner tie-breaking are represented. However, several material rules are contradicted or omitted, including planting traded cards, Ackerbohne rewards, Weinbrandbohne values, depletion timing, harvesting access, gifting, and private observations.

## Findings

### Major

1. **Only the active player plants traded/received cards**

- Fact: `P3-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Evidence: “Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen. Als aktiver Spieler musst du auch jede aufgedeckte Karte anbauen, die du nicht gehandelt hast.”
- Code: `current_player`, `legal_actions` branch `plant_incoming`, `finish_trading`, `finish_incoming`
- Expected: Every recipient plants all received cards, while the active player also plants retained revealed cards.
- Implemented: `finish_trading` changes directly to `plant_incoming`, but `current_player` remains `s.active`. Once the active player finishes, the game advances to `draw_each`; inactive players’ `incoming` cards remain unplanted indefinitely.

2. **Two Ackerbohnen incorrectly award two coins**

- Fact: `ACKER-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 11
- Evidence: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld. […] Die geernteten Ackerbohnen legst du auf den Ablagestapel.”
- Code: `_harvest`, especially `value = ... (2 if n == 2 and len(p.fields) == 2 else 0)`
- Expected: Exactly two Ackerbohnen unlock the third field, award zero coins, and both cards go to discard.
- Implemented: The third field is unlocked, but two coins are also awarded and no Ackerbohnen are discarded because `cards[value:]` is empty. This can directly change the winner and later deck contents.

3. **Weinbrandbohne Bohnometer is materially too generous**

- Fact: `GOLD-09`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/9/ernte`
- Evidence: `4→1, 7→2, 9→3, 11→4`
- Code: `BEANS["Weinbrandbohne"]`
- Expected: Zero below four, then 1/2/3/4 coins at 4/7/9/11+.
- Implemented: 1/2/3/4 coins at 2/4/6/8+. This affects a 22-card bean type and can substantially alter scoring.

4. **Deck depletion is detected one draw too late**

- Facts: `DECK-01`, `END-02`, `END-05`
- Evidence types: `human_decision`, `rule_quote`
- Sources:
  - `RULES`, PDF page 9: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
  - `RULES`, PDF page 9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - `END-05` approved decision: third depletion during phase 4 is terminal immediately after the draw that empties the pile, before another player draws.
- Code: `_draw`, `reveal_two`, `draw_one`
- Expected: Depletion occurs when the last card is drawn. First/second depletion immediately reshuffles discard; third depletion gets the phase-specific terminal treatment.
- Implemented: `_draw` increments `empty_count` only when a later draw starts with an already-empty deck.
  - A first/second depletion at the end of a reveal can postpone reshuffling until after trading and planting, allowing intervening discards into the reshuffle.
  - A third depletion on the second revealed card is not marked pending during phase 2.
  - A third depletion during phase 4 requires the next player to select `draw_one` before termination, contrary to the approved immediate boundary.
- This deviation partly depends on the approved human timing decisions, but also conflicts with the printed “last card”/“becomes empty” trigger.

5. **Private-hand observations are not correctly represented and trade actions leak opponents’ cards**

- Fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckst du dahinter.” Approved expectation: each owner sees their whole ordered hand; opponents see only its count unless voluntarily communicated.
- Code: `render`; `legal_actions` trade branch generating `request_hand`
- Expected: An observing player sees their own complete hand and only opponents’ hand counts.
- Implemented:
  - `render` has no observer argument and reveals only `current_player`’s hand, so inactive players cannot obtain their own private observation.
  - During offer construction, actions enumerate `tp.hand[i]` with exact bean names and indices, revealing the target’s entire hand to the active player.

6. **Inactive owners generally cannot harvest during another player’s turn**

- Fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Code: `legal_actions` calls `_harvest_actions(s, current_player(s))`
- Expected: Any owner may harvest between atomic steps, including during another player’s turn.
- Implemented: Harvest actions are offered only to the current actor—normally the active player, or temporarily an offer target. Other inactive players cannot harvest at the permitted boundaries.
- This is adjudication-dependent because the exact atomic timing is supplied by the approved human decision.

7. **A non-active player cannot give an unconditional gift to the active player**

- Fact: `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6
- Evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Code: `legal_actions`, `submit_offer` condition
- Expected: A nonempty gift is legal with recipient consent, including a gift from an inactive participant to the active player.
- Implemented: An offer can be submitted only if `give_hand` or `give_market` is nonempty—cards supplied by the active player. A request-only proposal, which would model the target gifting cards to the active player, cannot be submitted.

8. **Final raw coin totals are calculated only in a temporary copy and are not observable**

- Fact: `END-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr.”
- Code: `returns`, `render`
- Expected: Final fields are harvested, hands are ignored, and the resulting raw coin totals remain observable.
- Implemented: `returns` harvests into a local deep copy used only to determine ±1 returns. The terminal state and `render` continue to show pre-final-harvest fields and coin totals.

No critical or minor findings identified.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Covered | Correct 4–5 players, 129-card composition, five ordered cards |
| Turn order and phases | Partial | Basic order correct; post-trade participant sequencing is wrong |
| Phase-1 planting | Covered | Mandatory first, optional second, legal forced harvest path |
| Reveal and trade | Partial | Atomic acceptance and asymmetric quantities supported; privacy and one gift direction fail |
| Mandatory planting | Fails | Inactive recipients do not plant incoming cards |
| Phase-4 draws | Partial | One per player clockwise; depletion boundary wrong |
| Normal harvesting | Partial | Protection and normal conversion correct; inactive timing unavailable |
| Ackerbohne | Fails | Two-card harvest incorrectly pays two coins |
| Other Bohnometers | Partial | Base values correct; Weinbrandbohne incorrect |
| Private information | Fails | No observer-specific view; opponent hands leak through actions |
| Terminal and winner | Partial | Final winner/tie logic exists; depletion timing and observable final totals fail |
| Returns | Partial | Zero nonterminal and winner-based terminal returns supported |

## Missing deterministic scenarios

- A trade gives cards to both the active and inactive player; verify both complete mandatory planting before phase 4.
- Harvest exactly two Ackerbohnen with two fields: third field appears, zero coins, both cards enter discard.
- Harvest two Ackerbohnen after field 3 is already unlocked: zero reward and both discarded.
- Weinbrandbohne harvests at 2, 4, 6, 7, 9, and 11 cards.
- Draw the final deck card as the second phase-2 reveal on depletion one, two, and three.
- Draw the final deck card during each seat’s phase-4 draw on third depletion.
- Verify immediate reshuffle excludes cards discarded only during later trading/planting.
- Give a request-only, nonempty gift from an inactive player to the active player.
- Verify every player’s observation exposes their own ordered hand but only opponents’ counts.
- Attempt an inactive owner’s legal harvest between actions on another player’s turn.
- Terminal scoring where final field harvest changes the winner; verify final raw totals are observable.
- A five-player tied result verifying greatest clockwise distance from the original start player.

## Material questions for a human

- Is seat 0 intentionally defined as the externally chosen start player? The module has no configurable start-player parameter, but this can be a valid seat-normalization convention.
- Is `render` intended as the actual player observation API or only a debugging display? If it is debugging-only, a required observer-specific information interface appears to be absent rather than merely incorrect.

score: 0.38
confidence: high
critical_issues: 0
major_issues: 8
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true